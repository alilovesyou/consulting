import { useEffect, useState } from "react";
import Card from "../../components/Card";
import ListPager from "../../components/ListPager";
import SearchBox from "../../components/SearchBox";
import { paginate, getTotalPages, clampPage } from "../../utils/pagination";
import { t } from "../../i18n";

const PAGE_SIZE = 8;

export default function TeacherDashboard({ api, profile, lang = "uz" }) {
  const [activeSection, setActiveSection] = useState("home");

  const [groups, setGroups] = useState([]);
  const [students, setStudents] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [results, setResults] = useState([]);
  const [kickRequests, setKickRequests] = useState([]);

  const [studentsSearch, setStudentsSearch] = useState("");
  const [lessonsSearch, setLessonsSearch] = useState("");
  const [resultsSearch, setResultsSearch] = useState("");
  const [kicksSearch, setKicksSearch] = useState("");

  const [studentsPage, setStudentsPage] = useState(1);
  const [lessonsPage, setLessonsPage] = useState(1);
  const [resultsPage, setResultsPage] = useState(1);
  const [kicksPage, setKicksPage] = useState(1);

  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [selectedGroup, setSelectedGroup] = useState(null);

  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonFile, setLessonFile] = useState(null);

  const [resultStudentId, setResultStudentId] = useState("");
  const [resultTitle, setResultTitle] = useState("");
  const [score, setScore] = useState("");
  const [comment, setComment] = useState("");

  const [kickStudentId, setKickStudentId] = useState("");
  const [kickReason, setKickReason] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loadingAction, setLoadingAction] = useState(false);
  const [loadingGroup, setLoadingGroup] = useState(false);

  const tr = (key) => t(key, lang);

  useEffect(() => {
    loadHomeData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function searchList(items, query) {
    const q = query.trim().toLowerCase();

    if (!q) return items;

    return items.filter((item) =>
      Object.values(item || {})
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }

  function getPageData(items, page, search) {
    const filtered = searchList(items, search);
    const totalPages = getTotalPages(filtered, PAGE_SIZE);
    const safePage = clampPage(page, totalPages);
    const visible = paginate(filtered, safePage, PAGE_SIZE);

    return {
      filtered,
      totalPages,
      safePage,
      visible,
    };
  }

  async function loadHomeData() {
    try {
      setError("");

      const groupsRes = await api.get("/api/teacher/groups");
      const resultsRes = await api.get("/api/teacher/results");
      const kicksRes = await api.get("/api/teacher/kick-requests");

      setGroups(groupsRes.data.groups || []);
      setResults(resultsRes.data.results || []);
      setKickRequests(kicksRes.data.kick_requests || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadMiniAppFailed"));
    }
  }

  async function openSection(section) {
    setActiveSection(section);
    setError("");
    setSuccess("");

    if (section === "groups") {
      setStudentsPage(1);
      setLessonsPage(1);
      await loadHomeData();
    }

    if (section === "upload") {
      await loadHomeData();
      clearGroupData();
    }

    if (section === "results") {
      await loadHomeData();
      clearGroupData();
    }

    if (section === "kick") {
      await loadHomeData();
      clearGroupData();
    }

    if (section === "history") {
      setResultsPage(1);
      setKicksPage(1);
      await loadHomeData();
    }
  }

  function goHome() {
    setActiveSection("home");
    setError("");
    setSuccess("");
    clearGroupData();
  }

  function clearGroupData() {
    setSelectedGroupId("");
    setSelectedGroup(null);
    setStudents([]);
    setLessons([]);
    setStudentsSearch("");
    setLessonsSearch("");
    setStudentsPage(1);
    setLessonsPage(1);
  }

  async function selectGroup(groupId) {
    if (!groupId) {
      clearGroupData();
      return;
    }

    const group = groups.find((item) => String(item.id) === String(groupId));

    if (!group) {
      setError(tr("groupNotFound"));
      return;
    }

    try {
      setLoadingGroup(true);
      setError("");
      setSelectedGroupId(String(groupId));
      setSelectedGroup(group);
      setStudentsSearch("");
      setLessonsSearch("");
      setStudentsPage(1);
      setLessonsPage(1);

      const studentsRes = await api.get(`/api/teacher/groups/${group.id}/students`);
      const lessonsRes = await api.get(`/api/teacher/groups/${group.id}/lessons`);

      setStudents(studentsRes.data.students || []);
      setLessons(lessonsRes.data.lessons || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("groupDataLoadFailed"));
    } finally {
      setLoadingGroup(false);
    }
  }

  async function uploadLesson(e) {
    e.preventDefault();

    if (!selectedGroup) {
      setError(tr("groupRequired"));
      return;
    }

    if (!lessonTitle.trim()) {
      setError(tr("lessonTitleRequired"));
      return;
    }

    if (!lessonFile) {
      setError(tr("lessonFileRequired"));
      return;
    }

    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      const formData = new FormData();
      formData.append("title", lessonTitle.trim());
      formData.append("file", lessonFile);

      await api.post(`/api/teacher/groups/${selectedGroup.id}/lessons`, formData);

      setLessonTitle("");
      setLessonFile(null);
      setSuccess(tr("lessonUploadSuccess"));

      await selectGroup(selectedGroup.id);
    } catch (err) {
      setError(err.friendlyMessage || tr("lessonUploadFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  async function addResult(e) {
    e.preventDefault();

    if (!selectedGroup) {
      setError(tr("groupRequired"));
      return;
    }

    if (!resultStudentId) {
      setError(tr("studentRequired"));
      return;
    }

    if (!resultTitle.trim()) {
      setError(tr("resultTitleRequired"));
      return;
    }

    if (!score.trim()) {
      setError(tr("scoreRequired"));
      return;
    }

    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post(`/api/teacher/groups/${selectedGroup.id}/results`, {
        student_id: Number(resultStudentId),
        result_title: resultTitle.trim(),
        score: score.trim(),
        comment: comment.trim(),
      });

      setResultStudentId("");
      setResultTitle("");
      setScore("");
      setComment("");

      setSuccess(tr("addResultSuccess"));
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("addResultFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  async function sendKickRequest(e) {
    e.preventDefault();

    if (!selectedGroup) {
      setError(tr("groupRequired"));
      return;
    }

    if (!kickStudentId) {
      setError(tr("studentRequired"));
      return;
    }

    if (!kickReason.trim()) {
      setError(tr("reasonRequired"));
      return;
    }

    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post(`/api/teacher/groups/${selectedGroup.id}/kick-requests`, {
        student_id: Number(kickStudentId),
        reason: kickReason.trim(),
      });

      setKickStudentId("");
      setKickReason("");

      setSuccess(tr("kickRequestSuccess"));
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("kickRequestFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  function renderNotice() {
    return (
      <>
        {error && (
          <div className="noticeBox errorNotice">
            <b>{tr("error")}</b>
            <p>{error}</p>
          </div>
        )}

        {success && (
          <div className="noticeBox successNotice">
            <b>{tr("done")}</b>
            <p>{success}</p>
          </div>
        )}
      </>
    );
  }

  function renderBackHeader(title, subtitle) {
    return (
      <div className="sectionHeader">
        <button className="backButton" type="button" onClick={goHome}>
          {tr("back")}
        </button>

        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>
    );
  }

  function renderGroupSelect() {
    return (
      <Card title={tr("groupSelect")}>
        <div className="formBlock">
          <label>
            {tr("group")}
            <select
              value={selectedGroupId}
              onChange={(e) => selectGroup(e.target.value)}
            >
              <option value="">{tr("chooseGroup")}</option>
              {groups.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name} — {group.current_count}/{group.max_capacity}
                </option>
              ))}
            </select>
          </label>
        </div>

        {loadingGroup && <p className="muted">{tr("groupLoading")}</p>}

        {selectedGroup && (
          <div className="selectedGroupInfo">
            <b>{selectedGroup.name}</b>
            <p>{selectedGroup.language}</p>
            <span>
              {selectedGroup.current_count}/{selectedGroup.max_capacity}{" "}
              {tr("studentCount")}
            </span>
          </div>
        )}
      </Card>
    );
  }

  function renderHome() {
    const pendingKicks = kickRequests.filter((item) => item.status === "pending").length;

    return (
      <>
        <section className="profilePanel">
          <div>
            <p className="eyebrow">{tr("teacher")}</p>
            <h2>{profile.full_name || tr("fullNameMissing")}</h2>
            <p className="profileMeta">
              {tr("subject")}: {profile.teach_lang || "-"} · ID:{" "}
              {profile.telegram_id}
            </p>
          </div>
        </section>

        {renderNotice()}

        <section className="quickStats">
          <div>
            <b>{groups.length}</b>
            <span>{tr("groups")}</span>
          </div>
          <div>
            <b>{results.length}</b>
            <span>{tr("results")}</span>
          </div>
          <div>
            <b>{pendingKicks}</b>
            <span>{tr("pendingKick")}</span>
          </div>
        </section>

        <section className="menuGrid">
          <button
            className="menuTile icon-groups"
            type="button"
            onClick={() => openSection("groups")}
          >
            <span className="menuIcon"></span>
            <b>{tr("myGroups")}</b>
            <small>{tr("myGroupsDesc")}</small>
          </button>

          <button
            className="menuTile icon-upload"
            type="button"
            onClick={() => openSection("upload")}
          >
            <span className="menuIcon"></span>
            <b>{tr("uploadLesson")}</b>
            <small>{tr("uploadLessonDesc")}</small>
          </button>

          <button
            className="menuTile icon-results"
            type="button"
            onClick={() => openSection("results")}
          >
            <span className="menuIcon"></span>
            <b>{tr("addResult")}</b>
            <small>{tr("addResultDesc")}</small>
          </button>

          <button
            className="menuTile icon-kick"
            type="button"
            onClick={() => openSection("kick")}
          >
            <span className="menuIcon"></span>
            <b>{tr("kickRequest")}</b>
            <small>{tr("kickRequestDescTeacher")}</small>
          </button>

          <button
            className="menuTile icon-history wideTile"
            type="button"
            onClick={() => openSection("history")}
          >
            <span className="menuIcon"></span>
            <b>{tr("teacherHistory")}</b>
            <small>{tr("teacherHistoryDesc")}</small>
          </button>
        </section>
      </>
    );
  }

  function renderGroups() {
    const studentsData = getPageData(students, studentsPage, studentsSearch);
    const lessonsData = getPageData(lessons, lessonsPage, lessonsSearch);

    return (
      <>
        {renderBackHeader(tr("myGroups"), tr("myGroupsDesc"))}
        {renderNotice()}

        {groups.length === 0 ? (
          <div className="simpleEmpty">{tr("noGroupsAssigned")}</div>
        ) : (
          groups.map((group) => (
            <button
              key={group.id}
              className={
                selectedGroup?.id === group.id
                  ? "groupListBtn active"
                  : "groupListBtn"
              }
              type="button"
              onClick={() => selectGroup(group.id)}
            >
              <div>
                <b>{group.name}</b>
                <p>{group.language}</p>
              </div>
              <span>
                {group.current_count}/{group.max_capacity}
              </span>
            </button>
          ))
        )}

        {selectedGroup && (
          <>
            <Card title={tr("studentsInGroup")}>
              <SearchBox
                value={studentsSearch}
                onChange={(value) => {
                  setStudentsSearch(value);
                  setStudentsPage(1);
                }}
                placeholder={tr("searchStudents")}
              />

              {studentsData.filtered.length === 0 ? (
                <p>{tr("noStudentsFound")}</p>
              ) : (
                studentsData.visible.map((student) => (
                  <div key={student.telegram_id} className="compactListItem">
                    <b>{student.full_name || student.telegram_id}</b>
                    <p>{student.phone || "-"}</p>
                    <span>ID: {student.telegram_id}</span>
                  </div>
                ))
              )}

              <ListPager
                page={studentsData.safePage}
                totalPages={studentsData.totalPages}
                totalItems={studentsData.filtered.length}
                pageSize={PAGE_SIZE}
                onPrev={() => setStudentsPage(studentsData.safePage - 1)}
                onNext={() => setStudentsPage(studentsData.safePage + 1)}
              />
            </Card>

            <Card title={tr("lessonList")}>
              <SearchBox
                value={lessonsSearch}
                onChange={(value) => {
                  setLessonsSearch(value);
                  setLessonsPage(1);
                }}
                placeholder={tr("searchLessons")}
              />

              {lessonsData.filtered.length === 0 ? (
                <p>{tr("noLessonsFound")}</p>
              ) : (
                lessonsData.visible.map((lesson) => (
                  <div key={lesson.id} className="compactListItem">
                    <b>{lesson.title}</b>
                    <p>{lesson.material_type || "material"}</p>
                    {lesson.material_url && (
                      <a
                        className="fileLink"
                        href={lesson.material_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {tr("receiptOpen")}
                      </a>
                    )}
                  </div>
                ))
              )}

              <ListPager
                page={lessonsData.safePage}
                totalPages={lessonsData.totalPages}
                totalItems={lessonsData.filtered.length}
                pageSize={PAGE_SIZE}
                onPrev={() => setLessonsPage(lessonsData.safePage - 1)}
                onNext={() => setLessonsPage(lessonsData.safePage + 1)}
              />
            </Card>
          </>
        )}
      </>
    );
  }

  function renderUpload() {
    return (
      <>
        {renderBackHeader(tr("uploadLesson"), tr("uploadLessonDesc"))}
        {renderNotice()}
        {renderGroupSelect()}

        {selectedGroup && (
          <Card title={tr("newLesson")}>
            <form onSubmit={uploadLesson}>
              <div className="formBlock">
                <label>
                  {tr("lessonTitle")}
                  <input
                    value={lessonTitle}
                    onChange={(e) => setLessonTitle(e.target.value)}
                    placeholder={tr("lessonTitlePlaceholder")}
                  />
                </label>
              </div>

              <div className="formBlock">
                <label>
                  {tr("file")}
                  <input
                    type="file"
                    accept=".mp4,.mov,.mkv,.webm,.pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png,.webp"
                    onChange={(e) => setLessonFile(e.target.files?.[0] || null)}
                  />
                </label>
              </div>

              <button className="primaryAction" disabled={loadingAction}>
                {tr("upload")}
              </button>
            </form>
          </Card>
        )}
      </>
    );
  }

  function renderResults() {
    return (
      <>
        {renderBackHeader(tr("addResult"), tr("addResultDesc"))}
        {renderNotice()}
        {renderGroupSelect()}

        {selectedGroup && (
          <Card title={tr("newResult")}>
            <form onSubmit={addResult}>
              <div className="formBlock">
                <label>
                  {tr("student")}
                  <select
                    value={resultStudentId}
                    onChange={(e) => setResultStudentId(e.target.value)}
                  >
                    <option value="">{tr("chooseStudent")}</option>
                    {students.map((student) => (
                      <option key={student.telegram_id} value={student.telegram_id}>
                        {student.full_name || student.telegram_id}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="formBlock">
                <label>
                  {tr("resultTitle")}
                  <input
                    value={resultTitle}
                    onChange={(e) => setResultTitle(e.target.value)}
                    placeholder={tr("resultTitlePlaceholder")}
                  />
                </label>
              </div>

              <div className="formBlock">
                <label>
                  {tr("scoreResult")}
                  <input
                    value={score}
                    onChange={(e) => setScore(e.target.value)}
                    placeholder={tr("scorePlaceholder")}
                  />
                </label>
              </div>

              <div className="formBlock">
                <label>
                  {tr("comment")}
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder={tr("commentOptional")}
                    rows={3}
                  />
                </label>
              </div>

              <button className="primaryAction" disabled={loadingAction}>
                {tr("addResult")}
              </button>
            </form>
          </Card>
        )}
      </>
    );
  }

  function renderKick() {
    return (
      <>
        {renderBackHeader(tr("kickRequest"), tr("kickRequestDescTeacher"))}
        {renderNotice()}
        {renderGroupSelect()}

        {selectedGroup && (
          <Card title={tr("newRequest")}>
            <form onSubmit={sendKickRequest}>
              <div className="formBlock">
                <label>
                  {tr("student")}
                  <select
                    value={kickStudentId}
                    onChange={(e) => setKickStudentId(e.target.value)}
                  >
                    <option value="">{tr("chooseStudent")}</option>
                    {students.map((student) => (
                      <option key={student.telegram_id} value={student.telegram_id}>
                        {student.full_name || student.telegram_id}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="formBlock">
                <label>
                  {tr("reason")}
                  <textarea
                    value={kickReason}
                    onChange={(e) => setKickReason(e.target.value)}
                    placeholder={tr("reasonPlaceholder")}
                    rows={4}
                  />
                </label>
              </div>

              <button
                className="primaryAction dangerPrimaryAction"
                disabled={loadingAction}
              >
                {tr("sendRequest")}
              </button>
            </form>
          </Card>
        )}
      </>
    );
  }

  function renderHistory() {
    const resultsData = getPageData(results, resultsPage, resultsSearch);
    const kicksData = getPageData(kickRequests, kicksPage, kicksSearch);

    return (
      <>
        {renderBackHeader(tr("teacherHistory"), tr("teacherHistoryDesc"))}
        {renderNotice()}

        <Card title={tr("results")}>
          <SearchBox
            value={resultsSearch}
            onChange={(value) => {
              setResultsSearch(value);
              setResultsPage(1);
            }}
            placeholder={tr("searchResultsTeacher")}
          />

          {resultsData.filtered.length === 0 ? (
            <p>{tr("noResultsFound")}</p>
          ) : (
            resultsData.visible.map((result) => (
              <div key={result.id} className="compactListItem">
                <b>{result.student_name || result.user_id}</b>
                <p>
                  {result.result_title}: {result.score}
                </p>
                <span>{result.group_name || "-"}</span>
              </div>
            ))
          )}

          <ListPager
            page={resultsData.safePage}
            totalPages={resultsData.totalPages}
            totalItems={resultsData.filtered.length}
            pageSize={PAGE_SIZE}
            onPrev={() => setResultsPage(resultsData.safePage - 1)}
            onNext={() => setResultsPage(resultsData.safePage + 1)}
          />
        </Card>

        <Card title={tr("kickRequests")}>
          <SearchBox
            value={kicksSearch}
            onChange={(value) => {
              setKicksSearch(value);
              setKicksPage(1);
            }}
            placeholder={tr("searchKicksTeacher")}
          />

          {kicksData.filtered.length === 0 ? (
            <p>{tr("noKickRequestsFound")}</p>
          ) : (
            kicksData.visible.map((item) => (
              <div key={item.id} className="compactListItem">
                <b>{item.student_name || item.user_id}</b>
                <p>{item.reason}</p>
                <span>
                  {tr("status")}: {item.status}
                </span>
              </div>
            ))
          )}

          <ListPager
            page={kicksData.safePage}
            totalPages={kicksData.totalPages}
            totalItems={kicksData.filtered.length}
            pageSize={PAGE_SIZE}
            onPrev={() => setKicksPage(kicksData.safePage - 1)}
            onNext={() => setKicksPage(kicksData.safePage + 1)}
          />
        </Card>
      </>
    );
  }

  return (
    <>
      {activeSection === "home" && renderHome()}
      {activeSection === "groups" && renderGroups()}
      {activeSection === "upload" && renderUpload()}
      {activeSection === "results" && renderResults()}
      {activeSection === "kick" && renderKick()}
      {activeSection === "history" && renderHistory()}
    </>
  );
}
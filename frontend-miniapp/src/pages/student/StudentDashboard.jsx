import { useEffect, useState } from "react";
import Card from "../../components/Card";
import ListPager from "../../components/ListPager";
import SearchBox from "../../components/SearchBox";
import { paginate, getTotalPages, clampPage } from "../../utils/pagination";
import { t } from "../../i18n";

const PAGE_SIZE = 8;

export default function StudentDashboard({ api, profile, lang = "uz" }) {
  const [activeSection, setActiveSection] = useState("home");

  const [studentProfile, setStudentProfile] = useState(profile || null);
  const [groups, setGroups] = useState([]);
  const [results, setResults] = useState([]);

  const [groupsSearch, setGroupsSearch] = useState("");
  const [lessonsSearch, setLessonsSearch] = useState("");
  const [resultsSearch, setResultsSearch] = useState("");

  const [groupsPage, setGroupsPage] = useState(1);
  const [lessonsPage, setLessonsPage] = useState(1);
  const [resultsPage, setResultsPage] = useState(1);

  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [lessons, setLessons] = useState([]);

  const [loadingGroup, setLoadingGroup] = useState(false);
  const [error, setError] = useState("");

  const tr = (key) => t(key, lang);

  useEffect(() => {
    loadStudentData();
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

  function formatFileSize(size) {
    if (!size) return null;
    return `${(size / 1024 / 1024).toFixed(2)} MB`;
  }

  async function loadStudentData() {
    try {
      setError("");

      const profileRes = await api.get("/api/student/profile");
      const groupsRes = await api.get("/api/student/groups");
      const resultsRes = await api.get("/api/student/results");

      setStudentProfile(profileRes.data.profile || profile);
      setGroups(groupsRes.data.groups || []);
      setResults(resultsRes.data.results || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("studentDataLoadFailed"));
    }
  }

  async function openSection(section) {
    setActiveSection(section);
    setError("");

    if (section === "profile") {
      await loadStudentData();
    }

    if (section === "groups") {
      setGroupsPage(1);
      await loadStudentData();
    }

    if (section === "lessons") {
      setLessonsPage(1);
      await loadStudentData();
      clearSelectedGroup();
    }

    if (section === "results") {
      setResultsPage(1);
      await loadStudentData();
    }
  }

  function goHome() {
    setActiveSection("home");
    setError("");
    clearSelectedGroup();
  }

  function clearSelectedGroup() {
    setSelectedGroupId("");
    setSelectedGroup(null);
    setLessons([]);
    setLessonsSearch("");
    setLessonsPage(1);
  }

  async function selectGroup(groupId) {
    if (!groupId) {
      clearSelectedGroup();
      return;
    }

    const group = groups.find((item) => String(item.id) === String(groupId));

    if (!group) {
      setError(tr("groupNotFound"));
      return;
    }

    try {
      setError("");
      setLoadingGroup(true);
      setSelectedGroupId(String(groupId));
      setSelectedGroup(group);
      setLessons([]);
      setLessonsSearch("");
      setLessonsPage(1);

      const res = await api.get(`/api/student/groups/${group.id}/lessons`);
      setLessons(res.data.lessons || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("lessonsLoadFailed"));
    } finally {
      setLoadingGroup(false);
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

  function renderLessonMaterial(lesson) {
    if (!lesson.material_url) {
      return <p className="muted">{tr("lessonNoFile")}</p>;
    }

    if (lesson.material_type === "video") {
      return (
        <video controls className="media">
          <source src={lesson.material_url} />
          {tr("browserVideoUnsupported")}
        </video>
      );
    }

    if (lesson.material_type === "photo") {
      return (
        <img
          src={lesson.material_url}
          alt={lesson.title}
          className="media"
          loading="lazy"
        />
      );
    }

    return (
      <a
        className="fileLink"
        href={lesson.material_url}
        target="_blank"
        rel="noreferrer"
      >
        {tr("fileOpen")}
      </a>
    );
  }

  function renderHome() {
    return (
      <>
        <section className="profilePanel">
          <div>
            <p className="eyebrow">{tr("student")}</p>
            <h2>{studentProfile?.full_name || tr("fullNameMissing")}</h2>
            <p className="profileMeta">
              ID: {studentProfile?.telegram_id || profile?.telegram_id}
            </p>
          </div>
        </section>

        {renderNotice()}

        <section className="quickStats">
          <div>
            <b>{groups.length}</b>
            <span>{tr("groupsJoined")}</span>
          </div>
          <div>
            <b>{results.length}</b>
            <span>{tr("results")}</span>
          </div>
          <div>
            <b>{studentProfile?.role || "-"}</b>
            <span>{tr("studentStatus")}</span>
          </div>
        </section>

        <section className="menuGrid">
          <button
            className="menuTile icon-profile"
            type="button"
            onClick={() => openSection("profile")}
          >
            <span className="menuIcon"></span>
            <b>{tr("profile")}</b>
            <small>{tr("personalInfo")}</small>
          </button>

          <button
            className="menuTile icon-groups"
            type="button"
            onClick={() => openSection("groups")}
          >
            <span className="menuIcon"></span>
            <b>{tr("myGroups")}</b>
            <small>{tr("studentGroupsDesc")}</small>
          </button>

          <button
            className="menuTile icon-lessons"
            type="button"
            onClick={() => openSection("lessons")}
          >
            <span className="menuIcon"></span>
            <b>{tr("lessons")}</b>
            <small>{tr("studentLessonsDesc")}</small>
          </button>

          <button
            className="menuTile icon-results"
            type="button"
            onClick={() => openSection("results")}
          >
            <span className="menuIcon"></span>
            <b>{tr("results")}</b>
            <small>{tr("studentResultsDesc")}</small>
          </button>
        </section>
      </>
    );
  }

  function renderProfile() {
    return (
      <>
        {renderBackHeader(tr("profile"), tr("personalInfo"))}
        {renderNotice()}

        <section className="statsList">
          <div>
            <span>F.I.O</span>
            <b>{studentProfile?.full_name || "-"}</b>
          </div>
          <div>
            <span>{tr("phone")}</span>
            <b>{studentProfile?.phone || "-"}</b>
          </div>
          <div>
            <span>{tr("region")}</span>
            <b>{studentProfile?.region || "-"}</b>
          </div>
          <div>
            <span>{tr("age")}</span>
            <b>{studentProfile?.age || "-"}</b>
          </div>
          <div>
            <span>{tr("studentStatus")}</span>
            <b>{studentProfile?.role || "-"}</b>
          </div>
        </section>
      </>
    );
  }

  function renderGroups() {
    const data = getPageData(groups, groupsPage, groupsSearch);

    return (
      <>
        {renderBackHeader(tr("myGroups"), tr("studentGroupsDesc"))}
        {renderNotice()}

        <SearchBox
          value={groupsSearch}
          onChange={(value) => {
            setGroupsSearch(value);
            setGroupsPage(1);
          }}
          placeholder={tr("searchStudentGroups")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">{tr("noStudentGroups")}</div>
        ) : (
          data.visible.map((group) => (
            <div key={group.id} className="listItem">
              <div className="listTop">
                <div>
                  <b>{group.name}</b>
                  <p>{group.language}</p>
                </div>
                <span className="miniRole">
                  {group.current_count}/{group.max_capacity}
                </span>
              </div>

              <div className="listMeta">
                {tr("groupId")}: {group.id}
              </div>
            </div>
          ))
        )}

        <ListPager
          page={data.safePage}
          totalPages={data.totalPages}
          totalItems={data.filtered.length}
          pageSize={PAGE_SIZE}
          onPrev={() => setGroupsPage(data.safePage - 1)}
          onNext={() => setGroupsPage(data.safePage + 1)}
        />
      </>
    );
  }

  function renderLessons() {
    const data = getPageData(lessons, lessonsPage, lessonsSearch);

    return (
      <>
        {renderBackHeader(tr("lessons"), tr("studentLessonsDesc"))}
        {renderNotice()}

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
                    {group.name} — {group.language}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {loadingGroup && <p className="muted">{tr("lessonsLoading")}</p>}

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

        {selectedGroup && (
          <Card title={tr("lessonListStudent")}>
            <SearchBox
              value={lessonsSearch}
              onChange={(value) => {
                setLessonsSearch(value);
                setLessonsPage(1);
              }}
              placeholder={tr("searchStudentLessons")}
            />

            {data.filtered.length === 0 ? (
              <p>{tr("noLessonsInGroup")}</p>
            ) : (
              data.visible.map((lesson) => (
                <div key={lesson.id} className="lessonBox">
                  <h3>{lesson.title}</h3>

                  <p className="muted">
                    {tr("fileType")}: {lesson.material_type || "material"}
                  </p>

                  {lesson.original_filename && (
                    <p className="muted">
                      {tr("fileName")}: {lesson.original_filename}
                    </p>
                  )}

                  {lesson.file_size && (
                    <p className="muted">
                      {tr("fileSize")}: {formatFileSize(lesson.file_size)}
                    </p>
                  )}

                  {renderLessonMaterial(lesson)}
                </div>
              ))
            )}

            <ListPager
              page={data.safePage}
              totalPages={data.totalPages}
              totalItems={data.filtered.length}
              pageSize={PAGE_SIZE}
              onPrev={() => setLessonsPage(data.safePage - 1)}
              onNext={() => setLessonsPage(data.safePage + 1)}
            />
          </Card>
        )}
      </>
    );
  }

  function renderResults() {
    const data = getPageData(results, resultsPage, resultsSearch);

    return (
      <>
        {renderBackHeader(tr("results"), tr("studentResultsDesc"))}
        {renderNotice()}

        <SearchBox
          value={resultsSearch}
          onChange={(value) => {
            setResultsSearch(value);
            setResultsPage(1);
          }}
          placeholder={tr("searchStudentResults")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">{tr("noStudentResults")}</div>
        ) : (
          data.visible.map((result) => (
            <div key={result.id} className="listItem">
              <div className="listTop">
                <div>
                  <b>{result.result_title}</b>
                  <p>{result.group_name || "-"}</p>
                </div>
                <span className="miniRole approved">{result.score}</span>
              </div>

              <div className="listMeta">
                {tr("languageSubject")}: {result.group_language || "-"}
                <br />
                {tr("teacher")}: {result.teacher_name || "-"}
              </div>

              {result.comment && (
                <p className="wrappedText">
                  <b>{tr("comment")}:</b> {result.comment}
                </p>
              )}
            </div>
          ))
        )}

        <ListPager
          page={data.safePage}
          totalPages={data.totalPages}
          totalItems={data.filtered.length}
          pageSize={PAGE_SIZE}
          onPrev={() => setResultsPage(data.safePage - 1)}
          onNext={() => setResultsPage(data.safePage + 1)}
        />
      </>
    );
  }

  return (
    <>
      {activeSection === "home" && renderHome()}
      {activeSection === "profile" && renderProfile()}
      {activeSection === "groups" && renderGroups()}
      {activeSection === "lessons" && renderLessons()}
      {activeSection === "results" && renderResults()}
    </>
  );
}
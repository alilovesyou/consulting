import { useEffect, useState } from "react";
import Card from "../../components/Card";
import ListPager from "../../components/ListPager";
import SearchBox from "../../components/SearchBox";
import { paginate, getTotalPages, clampPage } from "../../utils/pagination";
import { t } from "../../i18n";

const PAGE_SIZE = 8;

export default function AdminDashboard({ api, profile, lang = "uz" }) {
  const [activeSection, setActiveSection] = useState("home");

  const [stats, setStats] = useState(null);
  const [payments, setPayments] = useState([]);
  const [groups, setGroups] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [applications, setApplications] = useState([]);
  const [kicks, setKicks] = useState([]);

  const [applicationsSearch, setApplicationsSearch] = useState("");
  const [groupsSearch, setGroupsSearch] = useState("");
  const [paymentsSearch, setPaymentsSearch] = useState("");
  const [kicksSearch, setKicksSearch] = useState("");
  const [teachersSearch, setTeachersSearch] = useState("");

  const [applicationsPage, setApplicationsPage] = useState(1);
  const [groupsPage, setGroupsPage] = useState(1);
  const [paymentsPage, setPaymentsPage] = useState(1);
  const [kicksPage, setKicksPage] = useState(1);
  const [teachersPage, setTeachersPage] = useState(1);

  const [groupName, setGroupName] = useState("");
  const [groupLanguage, setGroupLanguage] = useState("");
  const [groupCapacity, setGroupCapacity] = useState("10");
  const [groupLink, setGroupLink] = useState("");
  const [groupTeacherId, setGroupTeacherId] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loadingAction, setLoadingAction] = useState(false);

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

      const statsRes = await api.get("/api/admin/statistics");
      setStats(statsRes.data.statistics);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadAdminFailed"));
    }
  }

  async function openSection(section) {
    setActiveSection(section);
    setError("");
    setSuccess("");

    if (section === "applications") {
      setApplicationsPage(1);
      await loadApplications();
    }

    if (section === "groups") {
      setGroupsPage(1);
      await loadGroupsAndTeachers();
    }

    if (section === "payments") {
      setPaymentsPage(1);
      await loadPayments();
    }

    if (section === "kicks") {
      setKicksPage(1);
      await loadKicks();
    }

    if (section === "teachers") {
      setTeachersPage(1);
      await loadTeachers();
    }

    if (section === "stats") {
      await loadHomeData();
    }
  }

  function goHome() {
    setActiveSection("home");
    setError("");
    setSuccess("");
  }

  async function loadApplications() {
    try {
      const res = await api.get(
        "/api/admin/teacher-applications?status=pending_teacher"
      );
      setApplications(res.data.applications || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadTeacherApplicationsFailed"));
    }
  }

  async function loadGroupsAndTeachers() {
    try {
      const groupsRes = await api.get("/api/admin/groups");
      const teachersRes = await api.get("/api/admin/teachers");

      setGroups(groupsRes.data.groups || []);
      setTeachers(teachersRes.data.teachers || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadGroupsFailed"));
    }
  }

  async function loadTeachers() {
    try {
      const res = await api.get("/api/admin/teachers");
      setTeachers(res.data.teachers || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadTeachersFailed"));
    }
  }

  async function loadPayments() {
    try {
      const res = await api.get(
        "/api/accounting/payments?status=pending&payment_method=all&limit=100"
      );
      setPayments(res.data.payments || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadPaymentsFailed"));
    }
  }

  async function loadKicks() {
    try {
      const res = await api.get("/api/admin/kick-requests?status=pending");
      setKicks(res.data.kick_requests || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadKickRequestsFailed"));
    }
  }

  async function approveTeacher(teacherId) {
    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post(`/api/admin/teacher-applications/${teacherId}/approve`);

      setSuccess(tr("approveTeacherSuccess"));
      await loadApplications();
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("approveTeacherFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  async function rejectTeacher(teacherId) {
    const reason = window.prompt(tr("rejectReasonPrompt"));

    if (reason === null) return;

    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post(`/api/admin/teacher-applications/${teacherId}/reject`, {
        reason: reason.trim(),
      });

      setSuccess(tr("rejectTeacherSuccess"));
      await loadApplications();
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("rejectTeacherFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  async function createGroup(e) {
    e.preventDefault();

    if (!groupName.trim()) {
      setError(tr("groupNameRequired"));
      return;
    }

    if (!groupLanguage.trim()) {
      setError(tr("languageRequired"));
      return;
    }

    if (!groupCapacity || Number(groupCapacity) <= 0) {
      setError(tr("capacityInvalid"));
      return;
    }

    if (!groupLink.trim()) {
      setError(tr("telegramLinkRequired"));
      return;
    }

    if (!groupTeacherId) {
      setError(tr("teacherRequired"));
      return;
    }

    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post("/api/admin/groups", {
        name: groupName.trim(),
        language: groupLanguage.trim(),
        max_capacity: Number(groupCapacity),
        telegram_link: groupLink.trim(),
        teacher_id: Number(groupTeacherId),
      });

      setGroupName("");
      setGroupLanguage("");
      setGroupCapacity("10");
      setGroupLink("");
      setGroupTeacherId("");

      setSuccess(tr("createGroupSuccess"));
      await loadGroupsAndTeachers();
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("createGroupFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  async function deleteGroup(groupId) {
    const confirmed = window.confirm(tr("deleteGroupConfirm"));

    if (!confirmed) return;

    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.delete(`/api/admin/groups/${groupId}`);

      setSuccess(tr("deleteGroupSuccess"));
      await loadGroupsAndTeachers();
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("deleteGroupFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  async function approveKick(requestId) {
    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post(`/api/admin/kick-requests/${requestId}/approve`);

      setSuccess(tr("approveKickSuccess"));
      await loadKicks();
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("approveKickFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  async function rejectKick(requestId) {
    const reason = window.prompt(tr("rejectReasonPrompt"));

    if (reason === null) return;

    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post(`/api/admin/kick-requests/${requestId}/reject`, {
        reason: reason.trim(),
      });

      setSuccess(tr("rejectKickSuccess"));
      await loadKicks();
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("rejectKickFailed"));
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

  function renderHome() {
    return (
      <>
        <section className="profilePanel">
          <div>
            <p className="eyebrow">{tr("admin")}</p>
            <h2>{profile.full_name || tr("fullNameMissing")}</h2>
            <p className="profileMeta">
              {tr("telegramId")}: {profile.telegram_id}
            </p>
          </div>
        </section>

        {renderNotice()}

        <section className="quickStats">
          <div>
            <b>{stats?.pending_teachers ?? "-"}</b>
            <span>{tr("teacherApplicationShort")}</span>
          </div>
          <div>
            <b>{stats?.groups ?? "-"}</b>
            <span>{tr("groupListShort")}</span>
          </div>
          <div>
            <b>{stats?.pending_kicks ?? "-"}</b>
            <span>{tr("kickRequestShort")}</span>
          </div>
        </section>

        <section className="menuGrid">
          <button
            className="menuTile icon-teachers"
            type="button"
            onClick={() => openSection("applications")}
          >
            <span className="menuIcon"></span>
            <b>{tr("teacherApplications")}</b>
            <small>{tr("teacherApplicationsDesc")}</small>
          </button>

          <button
            className="menuTile icon-groups"
            type="button"
            onClick={() => openSection("groups")}
          >
            <span className="menuIcon"></span>
            <b>{tr("groups")}</b>
            <small>{tr("groupsDesc")}</small>
          </button>

          <button
            className="menuTile icon-payments"
            type="button"
            onClick={() => openSection("payments")}
          >
            <span className="menuIcon"></span>
            <b>{tr("payments")}</b>
            <small>{tr("paymentsDesc")}</small>
          </button>

          <button
            className="menuTile icon-kick"
            type="button"
            onClick={() => openSection("kicks")}
          >
            <span className="menuIcon"></span>
            <b>{tr("kickRequests")}</b>
            <small>{tr("kickRequestsDesc")}</small>
          </button>

          <button
            className="menuTile icon-staff"
            type="button"
            onClick={() => openSection("teachers")}
          >
            <span className="menuIcon"></span>
            <b>{tr("teachers")}</b>
            <small>{tr("teachersDesc")}</small>
          </button>

          <button
            className="menuTile icon-stats"
            type="button"
            onClick={() => openSection("stats")}
          >
            <span className="menuIcon"></span>
            <b>{tr("statistics")}</b>
            <small>{tr("statisticsDesc")}</small>
          </button>
        </section>
      </>
    );
  }

  function renderApplications() {
    const data = getPageData(applications, applicationsPage, applicationsSearch);

    return (
      <>
        {renderBackHeader(
          tr("teacherApplications"),
          tr("teacherApplicationsDesc")
        )}
        {renderNotice()}

        <SearchBox
          value={applicationsSearch}
          onChange={(value) => {
            setApplicationsSearch(value);
            setApplicationsPage(1);
          }}
          placeholder={tr("searchTeacherApplications")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">
            {tr("noPendingTeacherApplications")}
          </div>
        ) : (
          data.visible.map((teacher) => (
            <div key={teacher.telegram_id} className="listItem">
              <div className="listTop">
                <div>
                  <b>{teacher.full_name || tr("fullNameMissing")}</b>
                  <p>{teacher.phone || tr("phoneMissing")}</p>
                </div>
                <span className="miniRole pending">pending</span>
              </div>

              <div className="listMeta">
                ID: {teacher.telegram_id}
                <br />
                {tr("region")}: {teacher.region || "-"}
                <br />
                {tr("age")}: {teacher.age || "-"}
                <br />
                {tr("subject")}: {teacher.teach_lang || "-"}
              </div>

              {teacher.experience && (
                <p className="wrappedText">
                  <b>{tr("experience")}:</b> {teacher.experience}
                </p>
              )}

              <div className="roleActions">
                <button
                  disabled={loadingAction}
                  onClick={() => approveTeacher(teacher.telegram_id)}
                >
                  {tr("approve")}
                </button>

                <button
                  className="redMiniBtn"
                  disabled={loadingAction}
                  onClick={() => rejectTeacher(teacher.telegram_id)}
                >
                  {tr("reject")}
                </button>
              </div>
            </div>
          ))
        )}

        <ListPager
          page={data.safePage}
          totalPages={data.totalPages}
          totalItems={data.filtered.length}
          pageSize={PAGE_SIZE}
          onPrev={() => setApplicationsPage(data.safePage - 1)}
          onNext={() => setApplicationsPage(data.safePage + 1)}
        />
      </>
    );
  }

  function renderGroups() {
    const data = getPageData(groups, groupsPage, groupsSearch);

    return (
      <>
        {renderBackHeader(tr("groups"), tr("groupsDesc"))}
        {renderNotice()}

        <Card title={tr("newGroup")}>
          <form onSubmit={createGroup}>
            <div className="formBlock">
              <label>
                {tr("groupName")}
                <input
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  placeholder={tr("groupNamePlaceholder")}
                />
              </label>
            </div>

            <div className="formBlock">
              <label>
                {tr("languageSubject")}
                <input
                  value={groupLanguage}
                  onChange={(e) => setGroupLanguage(e.target.value)}
                  placeholder={tr("languageSubjectPlaceholder")}
                />
              </label>
            </div>

            <div className="formBlock">
              <label>
                {tr("capacity")}
                <input
                  type="number"
                  value={groupCapacity}
                  onChange={(e) => setGroupCapacity(e.target.value)}
                  min="1"
                />
              </label>
            </div>

            <div className="formBlock">
              <label>
                {tr("telegramGroupLink")}
                <input
                  value={groupLink}
                  onChange={(e) => setGroupLink(e.target.value)}
                  placeholder={tr("telegramGroupLinkPlaceholder")}
                />
              </label>
            </div>

            <div className="formBlock">
              <label>
                {tr("teacher")}
                <select
                  value={groupTeacherId}
                  onChange={(e) => setGroupTeacherId(e.target.value)}
                >
                  <option value="">{tr("chooseTeacher")}</option>
                  {teachers.map((teacher) => (
                    <option
                      key={teacher.telegram_id}
                      value={teacher.telegram_id}
                    >
                      {teacher.full_name || teacher.telegram_id} —{" "}
                      {teacher.teach_lang || "-"}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <button className="primaryAction" disabled={loadingAction}>
              {tr("createGroup")}
            </button>
          </form>
        </Card>

        <SearchBox
          value={groupsSearch}
          onChange={(value) => {
            setGroupsSearch(value);
            setGroupsPage(1);
          }}
          placeholder={tr("searchGroups")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">{tr("noGroupsFound")}</div>
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
                {tr("teacher")}: {group.teacher_name || "-"}
                <br />
                {tr("link")}: {group.telegram_link || "-"}
              </div>

              <div className="roleActions">
                <button
                  className="redMiniBtn"
                  disabled={loadingAction}
                  onClick={() => deleteGroup(group.id)}
                >
                  {tr("deleteGroup")}
                </button>
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

  function renderPayments() {
    const data = getPageData(payments, paymentsPage, paymentsSearch);

    return (
      <>
        {renderBackHeader(tr("pendingPayments"), tr("pendingPaymentsDesc"))}
        {renderNotice()}

        <SearchBox
          value={paymentsSearch}
          onChange={(value) => {
            setPaymentsSearch(value);
            setPaymentsPage(1);
          }}
          placeholder={tr("searchPayments")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">{tr("noPendingPaymentsFound")}</div>
        ) : (
          data.visible.map((payment) => (
            <div key={payment.id} className="listItem">
              <div className="listTop">
                <div>
                  <b>
                    {tr("payment")} #{payment.id}
                  </b>
                  <p>{payment.student_name || payment.user_id}</p>
                </div>
                <span className={`miniRole ${payment.payment_method}`}>
                  {payment.payment_method}
                </span>
              </div>

              <div className="listMeta">
                {tr("phone")}: {payment.student_phone || "-"}
                <br />
                {tr("course")}: {payment.course_info || "-"}
                <br />
                {tr("status")}: {payment.status}
              </div>

              {payment.receipt_url && (
                <a
                  className="fileLink"
                  href={payment.receipt_url}
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
          page={data.safePage}
          totalPages={data.totalPages}
          totalItems={data.filtered.length}
          pageSize={PAGE_SIZE}
          onPrev={() => setPaymentsPage(data.safePage - 1)}
          onNext={() => setPaymentsPage(data.safePage + 1)}
        />
      </>
    );
  }

  function renderKicks() {
    const data = getPageData(kicks, kicksPage, kicksSearch);

    return (
      <>
        {renderBackHeader(tr("kickRequests"), tr("kickRequestsDesc"))}
        {renderNotice()}

        <SearchBox
          value={kicksSearch}
          onChange={(value) => {
            setKicksSearch(value);
            setKicksPage(1);
          }}
          placeholder={tr("searchKicks")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">{tr("noPendingKickFound")}</div>
        ) : (
          data.visible.map((item) => (
            <div key={item.id} className="listItem">
              <div className="listTop">
                <div>
                  <b>
                    {tr("request")} #{item.id}
                  </b>
                  <p>{item.student_name || item.user_id}</p>
                </div>
                <span className="miniRole pending">pending</span>
              </div>

              <div className="listMeta">
                {tr("teacher")}: {item.teacher_name || item.teacher_id}
                <br />
                {tr("groups")}: {item.group_name || item.group_id}
              </div>

              <p className="wrappedText">
                <b>{tr("reason")}:</b> {item.reason}
              </p>

              <div className="roleActions">
                <button
                  disabled={loadingAction}
                  onClick={() => approveKick(item.id)}
                >
                  {tr("approve")}
                </button>

                <button
                  className="redMiniBtn"
                  disabled={loadingAction}
                  onClick={() => rejectKick(item.id)}
                >
                  {tr("reject")}
                </button>
              </div>
            </div>
          ))
        )}

        <ListPager
          page={data.safePage}
          totalPages={data.totalPages}
          totalItems={data.filtered.length}
          pageSize={PAGE_SIZE}
          onPrev={() => setKicksPage(data.safePage - 1)}
          onNext={() => setKicksPage(data.safePage + 1)}
        />
      </>
    );
  }

  function renderTeachers() {
    const data = getPageData(teachers, teachersPage, teachersSearch);

    return (
      <>
        {renderBackHeader(tr("teachers"), tr("teachersDesc"))}
        {renderNotice()}

        <SearchBox
          value={teachersSearch}
          onChange={(value) => {
            setTeachersSearch(value);
            setTeachersPage(1);
          }}
          placeholder={tr("searchTeachers")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">{tr("noTeachersFound")}</div>
        ) : (
          data.visible.map((teacher) => (
            <div key={teacher.telegram_id} className="listItem">
              <div className="listTop">
                <div>
                  <b>{teacher.full_name || tr("fullNameMissing")}</b>
                  <p>{teacher.phone || tr("phoneMissing")}</p>
                </div>
                <span className="miniRole teacher">teacher</span>
              </div>

              <div className="listMeta">
                ID: {teacher.telegram_id}
                <br />
                {tr("subject")}: {teacher.teach_lang || "-"}
                <br />
                {tr("region")}: {teacher.region || "-"}
              </div>
            </div>
          ))
        )}

        <ListPager
          page={data.safePage}
          totalPages={data.totalPages}
          totalItems={data.filtered.length}
          pageSize={PAGE_SIZE}
          onPrev={() => setTeachersPage(data.safePage - 1)}
          onNext={() => setTeachersPage(data.safePage + 1)}
        />
      </>
    );
  }

  function renderStats() {
    return (
      <>
        {renderBackHeader(tr("statistics"), tr("statisticsDesc"))}
        {renderNotice()}

        <section className="statsList">
          <div>
            <span>{tr("students")}</span>
            <b>{stats?.students ?? 0}</b>
          </div>
          <div>
            <span>{tr("teachers")}</span>
            <b>{stats?.teachers ?? 0}</b>
          </div>
          <div>
            <span>{tr("admins")}</span>
            <b>{stats?.admins ?? 0}</b>
          </div>
          <div>
            <span>{tr("accountants")}</span>
            <b>{stats?.accountants ?? 0}</b>
          </div>
          <div>
            <span>{tr("groups")}</span>
            <b>{stats?.groups ?? 0}</b>
          </div>
          <div>
            <span>{tr("pendingTeacher")}</span>
            <b>{stats?.pending_teachers ?? 0}</b>
          </div>
          <div>
            <span>{tr("pendingPayment")}</span>
            <b>{stats?.pending_payments ?? 0}</b>
          </div>
          <div>
            <span>{tr("approvedPayment")}</span>
            <b>{stats?.approved_payments ?? 0}</b>
          </div>
          <div>
            <span>{tr("rejectedPayment")}</span>
            <b>{stats?.rejected_payments ?? 0}</b>
          </div>
          <div>
            <span>{tr("pendingKick")}</span>
            <b>{stats?.pending_kicks ?? 0}</b>
          </div>
        </section>
      </>
    );
  }

  return (
    <>
      {activeSection === "home" && renderHome()}
      {activeSection === "applications" && renderApplications()}
      {activeSection === "groups" && renderGroups()}
      {activeSection === "payments" && renderPayments()}
      {activeSection === "kicks" && renderKicks()}
      {activeSection === "teachers" && renderTeachers()}
      {activeSection === "stats" && renderStats()}
    </>
  );
}
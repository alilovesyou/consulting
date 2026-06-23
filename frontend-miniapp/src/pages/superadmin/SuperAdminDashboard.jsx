import { useEffect, useState } from "react";
import Card from "../../components/Card";
import ListPager from "../../components/ListPager";
import SearchBox from "../../components/SearchBox";
import { paginate, getTotalPages, clampPage } from "../../utils/pagination";
import { t } from "../../i18n";

const PAGE_SIZE = 8;

export default function SuperAdminDashboard({ api, profile, lang = "uz" }) {
  const [activeSection, setActiveSection] = useState("home");

  const [stats, setStats] = useState(null);
  const [staff, setStaff] = useState([]);
  const [recentUsers, setRecentUsers] = useState([]);
  const [actions, setActions] = useState([]);

  const [staffRoleFilter, setStaffRoleFilter] = useState("");

  const [staffSearch, setStaffSearch] = useState("");
  const [recentSearch, setRecentSearch] = useState("");
  const [actionsSearch, setActionsSearch] = useState("");

  const [staffPage, setStaffPage] = useState(1);
  const [recentPage, setRecentPage] = useState(1);
  const [actionsPage, setActionsPage] = useState(1);

  const [manualTelegramId, setManualTelegramId] = useState("");
  const [manualFullName, setManualFullName] = useState("");
  const [manualRole, setManualRole] = useState("accountant");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loadingAction, setLoadingAction] = useState(false);

  const tr = (key) => t(key, lang);

  useEffect(() => {
    loadHomeData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function roleLabel(role) {
    if (role === "admin") return tr("admin");
    if (role === "accountant") return tr("accounting");
    if (role === "superadmin") return tr("superadmin");
    if (role === "user") return tr("userRole");
    return role || "-";
  }

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

      const statsRes = await api.get("/api/superadmin/statistics");
      setStats(statsRes.data.statistics);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadSuperadminFailed"));
    }
  }

  async function openSection(section) {
    setActiveSection(section);
    setError("");
    setSuccess("");

    if (section === "staff") {
      setStaffPage(1);
      await loadStaff("");
    }

    if (section === "recent") {
      setRecentPage(1);
      await loadRecentUsers();
    }

    if (section === "actions") {
      setActionsPage(1);
      await loadActions();
    }

    if (section === "stats") {
      await loadHomeData();
    }
  }

  async function loadStaff(role = "") {
    try {
      setError("");
      setStaffRoleFilter(role);

      const url = role
        ? `/api/superadmin/staff?role=${role}`
        : "/api/superadmin/staff";

      const res = await api.get(url);
      setStaff(res.data.staff || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadStaffFailed"));
    }
  }

  async function loadRecentUsers() {
    try {
      setError("");

      const res = await api.get("/api/superadmin/staff/recent-users?limit=100");
      setRecentUsers(res.data.users || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadRecentUsersFailed"));
    }
  }

  async function loadActions() {
    try {
      setError("");

      const res = await api.get("/api/superadmin/admin-actions?limit=100");
      setActions(res.data.actions || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadActionsFailed"));
    }
  }

  async function setUserRole(telegramId, role, fullName = null) {
    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post("/api/superadmin/staff/role", {
        telegram_id: Number(telegramId),
        role,
        full_name: fullName || null,
      });

      setSuccess(`${tr("roleChangedSuccess")}: ${telegramId} → ${roleLabel(role)}`);

      if (activeSection === "staff") {
        await loadStaff(staffRoleFilter);
      }

      if (activeSection === "recent") {
        await loadRecentUsers();
      }

      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("roleChangeFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  async function submitManualRole(e) {
    e.preventDefault();

    const telegramId = manualTelegramId.trim();

    if (!telegramId) {
      setError(tr("telegramIdRequired"));
      return;
    }

    if (!/^\d+$/.test(telegramId)) {
      setError(tr("telegramIdOnlyNumbers"));
      return;
    }

    await setUserRole(
      telegramId,
      manualRole,
      manualFullName.trim() || null
    );

    setManualTelegramId("");
    setManualFullName("");
    setManualRole("accountant");
  }

  function goHome() {
    setActiveSection("home");
    setError("");
    setSuccess("");
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
            <p className="eyebrow">{tr("superadmin")}</p>
            <h2>{profile.full_name || tr("fullNameMissing")}</h2>
            <p className="profileMeta">
              {tr("telegramId")}: {profile.telegram_id}
            </p>
          </div>
        </section>

        {renderNotice()}

        <section className="quickStats">
          <div>
            <b>{stats?.users?.total ?? "-"}</b>
            <span>{tr("users")}</span>
          </div>
          <div>
            <b>{stats?.users?.accountant ?? "-"}</b>
            <span>{tr("accounting")}</span>
          </div>
          <div>
            <b>{stats?.payments?.pending ?? "-"}</b>
            <span>{tr("pendingPayment")}</span>
          </div>
        </section>

        <section className="menuGrid">
          <button
            className="menuTile icon-staff"
            type="button"
            onClick={() => openSection("staff")}
          >
            <span className="menuIcon"></span>
            <b>{tr("staff")}</b>
            <small>{tr("staffDesc")}</small>
          </button>

          <button
            className="menuTile icon-role"
            type="button"
            onClick={() => openSection("role")}
          >
            <span className="menuIcon"></span>
            <b>{tr("roleManagement")}</b>
            <small>{tr("roleManagementDesc")}</small>
          </button>

          <button
            className="menuTile icon-recent"
            type="button"
            onClick={() => openSection("recent")}
          >
            <span className="menuIcon"></span>
            <b>{tr("recentUsers")}</b>
            <small>{tr("recentUsersDesc")}</small>
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

          <button
            className="menuTile icon-history wideTile"
            type="button"
            onClick={() => openSection("actions")}
          >
            <span className="menuIcon"></span>
            <b>{tr("actionHistory")}</b>
            <small>{tr("actionHistoryDesc")}</small>
          </button>
        </section>
      </>
    );
  }

  function renderRoleButtons(user) {
    return (
      <div className="roleActions">
        <button
          disabled={loadingAction}
          onClick={() => setUserRole(user.telegram_id, "admin", user.full_name)}
        >
          {tr("admin")}
        </button>

        <button
          disabled={loadingAction}
          onClick={() =>
            setUserRole(user.telegram_id, "accountant", user.full_name)
          }
        >
          {tr("accounting")}
        </button>

        <button
          disabled={loadingAction}
          onClick={() =>
            setUserRole(user.telegram_id, "superadmin", user.full_name)
          }
        >
          {tr("superadmin")}
        </button>

        <button
          className="redMiniBtn"
          disabled={loadingAction}
          onClick={() => setUserRole(user.telegram_id, "user", user.full_name)}
        >
          {tr("userRole")}
        </button>
      </div>
    );
  }

  function renderStaff() {
    const data = getPageData(staff, staffPage, staffSearch);

    return (
      <>
        {renderBackHeader(tr("staff"), tr("staffDesc"))}
        {renderNotice()}

        <div className="filterRow">
          <button
            className={!staffRoleFilter ? "filterBtn active" : "filterBtn"}
            type="button"
            onClick={() => {
              setStaffPage(1);
              loadStaff("");
            }}
          >
            {tr("allStaff")}
          </button>

          <button
            className={staffRoleFilter === "admin" ? "filterBtn active" : "filterBtn"}
            type="button"
            onClick={() => {
              setStaffPage(1);
              loadStaff("admin");
            }}
          >
            {tr("admin")}
          </button>

          <button
            className={
              staffRoleFilter === "accountant" ? "filterBtn active" : "filterBtn"
            }
            type="button"
            onClick={() => {
              setStaffPage(1);
              loadStaff("accountant");
            }}
          >
            {tr("accounting")}
          </button>

          <button
            className={
              staffRoleFilter === "superadmin" ? "filterBtn active" : "filterBtn"
            }
            type="button"
            onClick={() => {
              setStaffPage(1);
              loadStaff("superadmin");
            }}
          >
            {tr("superadmin")}
          </button>
        </div>

        <SearchBox
          value={staffSearch}
          onChange={(value) => {
            setStaffSearch(value);
            setStaffPage(1);
          }}
          placeholder={tr("searchStaff")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">{tr("noStaffFound")}</div>
        ) : (
          data.visible.map((item) => (
            <div key={item.telegram_id} className="listItem">
              <div className="listTop">
                <div>
                  <b>{item.full_name || tr("fullNameMissing")}</b>
                  <p>{item.phone || tr("phoneMissing")}</p>
                </div>
                <span className={`miniRole ${item.role}`}>
                  {roleLabel(item.role)}
                </span>
              </div>

              <div className="listMeta">
                {tr("telegramId")}: {item.telegram_id}
              </div>

              {renderRoleButtons(item)}
            </div>
          ))
        )}

        <ListPager
          page={data.safePage}
          totalPages={data.totalPages}
          totalItems={data.filtered.length}
          pageSize={PAGE_SIZE}
          onPrev={() => setStaffPage(data.safePage - 1)}
          onNext={() => setStaffPage(data.safePage + 1)}
        />
      </>
    );
  }

  function renderRoleForm() {
    return (
      <>
        {renderBackHeader(tr("roleManagement"), tr("roleManagementDesc"))}
        {renderNotice()}

        <Card>
          <form onSubmit={submitManualRole}>
            <div className="formBlock">
              <label>
                {tr("telegramId")}
                <input
                  value={manualTelegramId}
                  onChange={(e) => setManualTelegramId(e.target.value)}
                  placeholder="123456789"
                  inputMode="numeric"
                />
              </label>
            </div>

            <div className="formBlock">
              <label>
                {tr("name")}
                <input
                  value={manualFullName}
                  onChange={(e) => setManualFullName(e.target.value)}
                  placeholder={tr("nameOptional")}
                />
              </label>
            </div>

            <div className="formBlock">
              <label>
                {tr("role")}
                <select
                  value={manualRole}
                  onChange={(e) => setManualRole(e.target.value)}
                >
                  <option value="admin">{tr("admin")}</option>
                  <option value="accountant">{tr("accounting")}</option>
                  <option value="superadmin">{tr("superadmin")}</option>
                  <option value="user">{tr("userRole")}</option>
                </select>
              </label>
            </div>

            <button className="primaryAction" disabled={loadingAction}>
              {tr("save")}
            </button>
          </form>
        </Card>
      </>
    );
  }

  function renderRecentUsers() {
    const data = getPageData(recentUsers, recentPage, recentSearch);

    return (
      <>
        {renderBackHeader(tr("recentUsers"), tr("recentUsersDesc"))}
        {renderNotice()}

        <SearchBox
          value={recentSearch}
          onChange={(value) => {
            setRecentSearch(value);
            setRecentPage(1);
          }}
          placeholder={tr("searchRecentUsers")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">{tr("noUsersFound")}</div>
        ) : (
          data.visible.map((user) => (
            <div key={user.telegram_id} className="listItem">
              <div className="listTop">
                <div>
                  <b>{user.full_name || tr("fullNameMissing")}</b>
                  <p>{user.phone || tr("phoneMissing")}</p>
                </div>
                <span className={`miniRole ${user.role || "user"}`}>
                  {roleLabel(user.role || "user")}
                </span>
              </div>

              <div className="listMeta">
                {tr("telegramId")}: {user.telegram_id}
              </div>

              {renderRoleButtons(user)}
            </div>
          ))
        )}

        <ListPager
          page={data.safePage}
          totalPages={data.totalPages}
          totalItems={data.filtered.length}
          pageSize={PAGE_SIZE}
          onPrev={() => setRecentPage(data.safePage - 1)}
          onNext={() => setRecentPage(data.safePage + 1)}
        />
      </>
    );
  }

  function renderStats() {
    return (
      <>
        {renderBackHeader(tr("statistics"), tr("superadminDesc"))}
        {renderNotice()}

        <section className="statsList">
          <div>
            <span>{tr("totalUsers")}</span>
            <b>{stats?.users?.total ?? 0}</b>
          </div>
          <div>
            <span>{tr("student")}</span>
            <b>{stats?.users?.student ?? 0}</b>
          </div>
          <div>
            <span>{tr("teacher")}</span>
            <b>{stats?.users?.teacher ?? 0}</b>
          </div>
          <div>
            <span>{tr("admin")}</span>
            <b>{stats?.users?.admin ?? 0}</b>
          </div>
          <div>
            <span>{tr("accounting")}</span>
            <b>{stats?.users?.accountant ?? 0}</b>
          </div>
          <div>
            <span>{tr("superadmin")}</span>
            <b>{stats?.users?.superadmin ?? 0}</b>
          </div>
          <div>
            <span>{tr("activeGroups")}</span>
            <b>{stats?.groups?.active ?? 0}</b>
          </div>
          <div>
            <span>{tr("pendingPayment")}</span>
            <b>{stats?.payments?.pending ?? 0}</b>
          </div>
          <div>
            <span>{tr("approvedPayment")}</span>
            <b>{stats?.payments?.approved ?? 0}</b>
          </div>
          <div>
            <span>{tr("rejectedPayment")}</span>
            <b>{stats?.payments?.rejected ?? 0}</b>
          </div>
        </section>
      </>
    );
  }

  function renderActions() {
    const data = getPageData(actions, actionsPage, actionsSearch);

    return (
      <>
        {renderBackHeader(tr("actionHistory"), tr("actionHistoryDesc"))}
        {renderNotice()}

        <SearchBox
          value={actionsSearch}
          onChange={(value) => {
            setActionsSearch(value);
            setActionsPage(1);
          }}
          placeholder={tr("searchActions")}
        />

        {data.filtered.length === 0 ? (
          <div className="simpleEmpty">{tr("noActionsFound")}</div>
        ) : (
          data.visible.map((action) => (
            <div key={action.id} className="listItem">
              <div className="listTop">
                <div>
                  <b>#{action.id} — {action.action}</b>
                  <p>{action.admin_name || action.admin_id}</p>
                </div>
              </div>

              <div className="listMeta">
                {tr("entity")}: {action.entity_type || "-"} /{" "}
                {action.entity_id || "-"}
              </div>
            </div>
          ))
        )}

        <ListPager
          page={data.safePage}
          totalPages={data.totalPages}
          totalItems={data.filtered.length}
          pageSize={PAGE_SIZE}
          onPrev={() => setActionsPage(data.safePage - 1)}
          onNext={() => setActionsPage(data.safePage + 1)}
        />
      </>
    );
  }

  return (
    <>
      {activeSection === "home" && renderHome()}
      {activeSection === "staff" && renderStaff()}
      {activeSection === "role" && renderRoleForm()}
      {activeSection === "recent" && renderRecentUsers()}
      {activeSection === "stats" && renderStats()}
      {activeSection === "actions" && renderActions()}
    </>
  );
}
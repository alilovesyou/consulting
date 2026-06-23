import { useEffect, useState } from "react";
import { t } from "../../i18n";

const PAGE_SIZE = 10;

export default function AccountantDashboard({ api, profile, lang = "uz" }) {
  const [activeSection, setActiveSection] = useState("home");

  const [stats, setStats] = useState(null);
  const [payments, setPayments] = useState([]);
  const [groups, setGroups] = useState([]);

  const [currentStatus, setCurrentStatus] = useState("pending");
  const [currentMethod, setCurrentMethod] = useState("all");
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);

  const [selectedGroups, setSelectedGroups] = useState({});

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loadingAction, setLoadingAction] = useState(false);
  const [loadingList, setLoadingList] = useState(false);

  const tr = (key) => t(key, lang);

  useEffect(() => {
    loadHomeData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadHomeData() {
    try {
      setError("");

      const statsRes = await api.get("/api/accounting/stats");
      setStats(statsRes.data.statistics);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadAccountingFailed"));
    }
  }

  async function openSection(section) {
    setActiveSection(section);
    setError("");
    setSuccess("");

    if (section === "pending") {
      await loadPayments("pending", "all", 1);
      await loadGroups();
    }

    if (section === "cash") {
      await loadPayments("pending", "cash", 1);
      await loadGroups();
    }

    if (section === "card") {
      await loadPayments("pending", "card", 1);
      await loadGroups();
    }

    if (section === "approved") {
      await loadPayments("approved", "all", 1);
    }

    if (section === "rejected") {
      await loadPayments("rejected", "all", 1);
    }

    if (section === "history") {
      await loadPayments("all", "all", 1);
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

  async function loadGroups() {
    try {
      const res = await api.get("/api/accounting/groups");
      setGroups(res.data.groups || []);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadGroupsFailed"));
    }
  }

  async function loadPayments(status, method, nextPage) {
    try {
      setLoadingList(true);
      setError("");
      setSuccess("");

      const offset = (nextPage - 1) * PAGE_SIZE;

      const res = await api.get(
        `/api/accounting/payments?status=${status}&payment_method=${method}&limit=${
          PAGE_SIZE + 1
        }&offset=${offset}`
      );

      const list = res.data.payments || [];

      setPayments(list.slice(0, PAGE_SIZE));
      setHasNext(list.length > PAGE_SIZE);
      setCurrentStatus(status);
      setCurrentMethod(method);
      setPage(nextPage);
    } catch (err) {
      setError(err.friendlyMessage || tr("loadPaymentsFailed"));
    } finally {
      setLoadingList(false);
    }
  }

  function setPaymentGroup(paymentId, groupId) {
    setSelectedGroups((prev) => ({
      ...prev,
      [paymentId]: groupId,
    }));
  }

  async function approvePayment(paymentId) {
    const groupId = selectedGroups[paymentId];

    if (!groupId) {
      setError(tr("groupRequiredForApprove"));
      return;
    }

    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post(`/api/accounting/payments/${paymentId}/approve`, {
        group_id: Number(groupId),
      });

      setSuccess(`${tr("approvePaymentSuccess")} #${paymentId}`);
      await loadPayments(currentStatus, currentMethod, page);
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("approvePaymentFailed"));
    } finally {
      setLoadingAction(false);
    }
  }

  async function rejectPayment(paymentId) {
    const reason = window.prompt(tr("rejectReasonPrompt"));

    if (reason === null) return;

    if (!reason.trim()) {
      setError(tr("rejectReasonRequired"));
      return;
    }

    try {
      setLoadingAction(true);
      setError("");
      setSuccess("");

      await api.post(`/api/accounting/payments/${paymentId}/reject`, {
        reason: reason.trim(),
      });

      setSuccess(`${tr("rejectPaymentSuccess")} #${paymentId}`);
      await loadPayments(currentStatus, currentMethod, page);
      await loadHomeData();
    } catch (err) {
      setError(err.friendlyMessage || tr("rejectPaymentFailed"));
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
            <p className="eyebrow">{tr("accounting")}</p>
            <h2>{profile.full_name || tr("fullNameMissing")}</h2>
            <p className="profileMeta">
              {tr("telegramId")}: {profile.telegram_id}
            </p>
          </div>
        </section>

        {renderNotice()}

        <section className="quickStats">
          <div>
            <b>{stats?.pending ?? "-"}</b>
            <span>{tr("pending")}</span>
          </div>
          <div>
            <b>{stats?.cash_pending ?? "-"}</b>
            <span>{tr("cash")}</span>
          </div>
          <div>
            <b>{stats?.card_pending ?? "-"}</b>
            <span>{tr("card")}</span>
          </div>
        </section>

        <section className="menuGrid">
          <button
            className="menuTile icon-pending"
            type="button"
            onClick={() => openSection("pending")}
          >
            <span className="menuIcon"></span>
            <b>{tr("pendingPayments")}</b>
            <small>{tr("pendingPaymentsDescAccounting")}</small>
          </button>

          <button
            className="menuTile icon-cash"
            type="button"
            onClick={() => openSection("cash")}
          >
            <span className="menuIcon"></span>
            <b>{tr("cashPayments")}</b>
            <small>{tr("cashPaymentsDesc")}</small>
          </button>

          <button
            className="menuTile icon-card"
            type="button"
            onClick={() => openSection("card")}
          >
            <span className="menuIcon"></span>
            <b>{tr("cardPayments")}</b>
            <small>{tr("cardPaymentsDesc")}</small>
          </button>

          <button
            className="menuTile icon-approved"
            type="button"
            onClick={() => openSection("approved")}
          >
            <span className="menuIcon"></span>
            <b>{tr("approved")}</b>
            <small>{tr("approvedPaymentsDesc")}</small>
          </button>

          <button
            className="menuTile icon-rejected"
            type="button"
            onClick={() => openSection("rejected")}
          >
            <span className="menuIcon"></span>
            <b>{tr("rejected")}</b>
            <small>{tr("rejectedPaymentsDesc")}</small>
          </button>

          <button
            className="menuTile icon-stats"
            type="button"
            onClick={() => openSection("stats")}
          >
            <span className="menuIcon"></span>
            <b>{tr("statistics")}</b>
            <small>{tr("paymentStatistics")}</small>
          </button>

          <button
            className="menuTile icon-history wideTile"
            type="button"
            onClick={() => openSection("history")}
          >
            <span className="menuIcon"></span>
            <b>{tr("paymentHistory")}</b>
            <small>{tr("paymentHistoryDesc")}</small>
          </button>
        </section>
      </>
    );
  }

  function sectionTitle() {
    if (activeSection === "pending") return tr("pendingPayments");
    if (activeSection === "cash") return tr("cashPayments");
    if (activeSection === "card") return tr("cardPayments");
    if (activeSection === "approved") return tr("approvedPayments");
    if (activeSection === "rejected") return tr("rejectedPayments");
    if (activeSection === "history") return tr("paymentHistory");
    return tr("payments");
  }

  function sectionSubtitle() {
    if (activeSection === "pending") return tr("pendingPaymentsDescAccounting");
    if (activeSection === "cash") return tr("cashPaymentsDesc");
    if (activeSection === "card") return tr("cardPaymentsDesc");
    if (activeSection === "approved") return tr("approvedPaymentsDesc");
    if (activeSection === "rejected") return tr("rejectedPaymentsDesc");
    if (activeSection === "history") return tr("paymentHistoryDesc");
    return "";
  }

  function canProcessPayment(payment) {
    return payment.status === "pending";
  }

  function renderPayments() {
    return (
      <>
        {renderBackHeader(sectionTitle(), sectionSubtitle())}
        {renderNotice()}

        <div className="filterRow">
          <button
            className={
              currentStatus === "pending" && currentMethod === "all"
                ? "filterBtn active"
                : "filterBtn"
            }
            type="button"
            onClick={() => loadPayments("pending", "all", 1)}
          >
            {tr("pending")}
          </button>

          <button
            className={
              currentStatus === "pending" && currentMethod === "cash"
                ? "filterBtn active"
                : "filterBtn"
            }
            type="button"
            onClick={() => loadPayments("pending", "cash", 1)}
          >
            {tr("cash")}
          </button>

          <button
            className={
              currentStatus === "pending" && currentMethod === "card"
                ? "filterBtn active"
                : "filterBtn"
            }
            type="button"
            onClick={() => loadPayments("pending", "card", 1)}
          >
            {tr("card")}
          </button>

          <button
            className={currentStatus === "approved" ? "filterBtn active" : "filterBtn"}
            type="button"
            onClick={() => loadPayments("approved", "all", 1)}
          >
            {tr("approved")}
          </button>

          <button
            className={currentStatus === "rejected" ? "filterBtn active" : "filterBtn"}
            type="button"
            onClick={() => loadPayments("rejected", "all", 1)}
          >
            {tr("rejected")}
          </button>

          <button
            className={currentStatus === "all" ? "filterBtn active" : "filterBtn"}
            type="button"
            onClick={() => loadPayments("all", "all", 1)}
          >
            {tr("all")}
          </button>
        </div>

        {loadingList ? (
          <div className="simpleEmpty">{tr("loading")}</div>
        ) : payments.length === 0 ? (
          <div className="simpleEmpty">{tr("paymentNotFound")}</div>
        ) : (
          payments.map((payment) => (
            <div key={payment.id} className="listItem">
              <div className="listTop">
                <div>
                  <b>
                    {tr("payment")} #{payment.id}
                  </b>
                  <p>{payment.student_name || payment.user_id}</p>
                </div>

                <span className={`miniRole ${payment.status}`}>
                  {payment.status}
                </span>
              </div>

              <div className="listMeta">
                {tr("phone")}: {payment.student_phone || "-"}
                <br />
                {tr("course")}: {payment.course_info || "-"}
                <br />
                {tr("paymentType")}: {payment.payment_method || "-"}
                <br />
                {tr("amount")}: {payment.amount || "-"}
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

              {canProcessPayment(payment) && (
                <>
                  <div className="formBlock">
                    <label>
                      {tr("group")}
                      <select
                        value={selectedGroups[payment.id] || ""}
                        onChange={(e) =>
                          setPaymentGroup(payment.id, e.target.value)
                        }
                      >
                        <option value="">{tr("chooseGroup")}</option>
                        {groups.map((group) => (
                          <option key={group.id} value={group.id}>
                            {group.name} — {group.current_count}/
                            {group.max_capacity}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <div className="roleActions">
                    <button
                      disabled={loadingAction}
                      onClick={() => approvePayment(payment.id)}
                    >
                      {tr("approve")}
                    </button>

                    <button
                      className="redMiniBtn"
                      disabled={loadingAction}
                      onClick={() => rejectPayment(payment.id)}
                    >
                      {tr("reject")}
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}

        <div className="pagination">
          <button
            className="pageBtn"
            type="button"
            disabled={page <= 1 || loadingList}
            onClick={() => loadPayments(currentStatus, currentMethod, page - 1)}
          >
            {tr("prev")}
          </button>

          <span className="pageNumber">
            {tr("page")} {page}
          </span>

          <button
            className="pageBtn"
            type="button"
            disabled={!hasNext || loadingList}
            onClick={() => loadPayments(currentStatus, currentMethod, page + 1)}
          >
            {tr("next")}
          </button>
        </div>
      </>
    );
  }

  function renderStats() {
    return (
      <>
        {renderBackHeader(tr("paymentStatistics"), tr("accountingDesc"))}
        {renderNotice()}

        <section className="statsList">
          <div>
            <span>{tr("total")}</span>
            <b>{stats?.total ?? 0}</b>
          </div>
          <div>
            <span>{tr("pending")}</span>
            <b>{stats?.pending ?? 0}</b>
          </div>
          <div>
            <span>{tr("approved")}</span>
            <b>{stats?.approved ?? 0}</b>
          </div>
          <div>
            <span>{tr("rejected")}</span>
            <b>{stats?.rejected ?? 0}</b>
          </div>
          <div>
            <span>{tr("cashPending")}</span>
            <b>{stats?.cash_pending ?? 0}</b>
          </div>
          <div>
            <span>{tr("cardPending")}</span>
            <b>{stats?.card_pending ?? 0}</b>
          </div>
        </section>
      </>
    );
  }

  return (
    <>
      {activeSection === "home" && renderHome()}

      {["pending", "cash", "card", "approved", "rejected", "history"].includes(
        activeSection
      ) && renderPayments()}

      {activeSection === "stats" && renderStats()}
    </>
  );
}
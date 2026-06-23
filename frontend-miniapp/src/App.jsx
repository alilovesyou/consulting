// frontend-miniapp/src/App.jsx
import { useEffect, useMemo, useState } from "react";
import "./App.css";

import { useTelegram } from "./hooks/useTelegram";
import { createApiClient } from "./services/api";
import { t } from "./i18n";

import Layout from "./components/Layout";
import Loading from "./components/Loading";
import ErrorBox from "./components/ErrorBox";

import StudentDashboard from "./pages/student/StudentDashboard";
import TeacherDashboard from "./pages/teacher/TeacherDashboard";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AccountantDashboard from "./pages/accountant/AccountantDashboard";
import SuperAdminPortal from "./pages/superadmin/SuperAdminPortal";

function App() {
  const { initTelegram, initData } = useTelegram();

  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const api = useMemo(() => createApiClient(initData), [initData]);

const profile = me?.profile || null;
const role = me?.role || "user";
const lang = profile?.interface_lang || "uz";

  useEffect(() => {
    initTelegram();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function loadMe() {
      try {
        setLoading(true);
        setError("");

        const res = await api.get("/api/me");

        if (isMounted) {
          setMe(res.data);
        }
      } catch (err) {
        if (isMounted) {
          setError(
            err.friendlyMessage ||
              err.response?.data?.detail ||
              t("loadMiniAppFailed", "uz")
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadMe();

    return () => {
      isMounted = false;
    };
  }, [api]);

if (loading) {
  return <Loading lang={lang} />;
}

if (error) {
  return <ErrorBox message={error} lang={lang} />;
}

  if (!profile) {
    return <ErrorBox message={t("profileNotFound", lang)} lang={lang} />;
  }

  let title = t("cabinet", lang);

  if (role === "student") title = t("studentCabinet", lang);
  if (role === "teacher") title = t("teacherCabinet", lang);
  if (role === "admin") title = t("adminCabinet", lang);
  if (role === "accountant") title = t("accountantCabinet", lang);
  if (role === "superadmin") title = t("superadminCabinet", lang);

  const activeRoles = [
    "student",
    "teacher",
    "admin",
    "accountant",
    "superadmin",
  ];

  return (
    <Layout profile={profile} title={title}>
      {role === "student" && (
        <StudentDashboard api={api} profile={profile} lang={lang} />
      )}

      {role === "teacher" && (
        <TeacherDashboard api={api} profile={profile} lang={lang} />
      )}

      {role === "admin" && (
        <AdminDashboard api={api} profile={profile} lang={lang} />
      )}

      {role === "accountant" && (
        <AccountantDashboard api={api} profile={profile} lang={lang} />
      )}

      {role === "superadmin" && (
        <SuperAdminPortal api={api} profile={profile} lang={lang} />
      )}

      {!activeRoles.includes(role) && (
        <section className="card">
          <h2>{t("inactiveProfile", lang)}</h2>
          <p>{t("inactiveProfileText", lang)}</p>
        </section>
      )}
    </Layout>
  );
}

export default App;
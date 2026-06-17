import { useEffect, useMemo, useState } from "react";
import "./App.css";

import { useTelegram } from "./hooks/useTelegram";
import { createApiClient } from "./services/api";

import Layout from "./components/Layout";
import Loading from "./components/Loading";
import ErrorBox from "./components/ErrorBox";

import StudentDashboard from "./pages/student/StudentDashboard";
import TeacherDashboard from "./pages/teacher/TeacherDashboard";
import AdminDashboard from "./pages/admin/AdminDashboard";
import SuperAdminDashboard from "./pages/superadmin/SuperAdminDashboard";

function App() {
  const { initTelegram, initData } = useTelegram();

  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const api = useMemo(() => createApiClient(initData), [initData]);

  useEffect(() => {
    initTelegram();
    loadMe();
  }, []);

  async function loadMe() {
    try {
      setLoading(true);
      setError("");

      const res = await api.get("/api/me");
      setMe(res.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Mini App ma'lumotlarini yuklab bo'lmadi."
      );
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <Loading />;

  if (error) return <ErrorBox message={error} />;

  const profile = me?.profile;
  const role = me?.role;

  if (!profile) {
    return <ErrorBox message="Profil topilmadi." />;
  }

  let title = "Kabinet";

  if (role === "student") title = "O‘quvchi kabineti";
  if (role === "teacher") title = "Ustoz kabineti";
  if (role === "admin") title = "Admin kabineti";
  if (role === "superadmin") title = "Superadmin kabineti";

  return (
    <Layout profile={profile} title={title}>
      {role === "student" && <StudentDashboard api={api} profile={profile} />}
      {role === "teacher" && <TeacherDashboard api={api} profile={profile} />}
      {role === "admin" && <AdminDashboard api={api} profile={profile} />}
      {role === "superadmin" && <SuperAdminDashboard api={api} profile={profile} />}

      {!["student", "teacher", "admin", "superadmin"].includes(role) && (
        <section className="card">
          <h2>Profil aktiv emas</h2>
          <p>
            Siz hali o‘quvchi, ustoz yoki admin sifatida tasdiqlanmagansiz.
            Iltimos, Telegram bot orqali ro‘yxatdan o‘ting.
          </p>
        </section>
      )}
    </Layout>
  );
}

export default App;
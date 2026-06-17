import { useEffect, useState } from "react";
import Card from "../../components/Card";

export default function SuperAdminDashboard({ api, profile }) {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [admins, setAdmins] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    loadSuperAdminData();
  }, []);

  async function loadSuperAdminData() {
    try {
      const statsRes = await api.get("/api/superadmin/statistics");
      const usersRes = await api.get("/api/superadmin/users?limit=20");
      const adminsRes = await api.get("/api/superadmin/admins");

      setStats(statsRes.data.statistics);
      setUsers(usersRes.data.users || []);
      setAdmins(adminsRes.data.admins || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Superadmin ma'lumotlarini yuklab bo'lmadi.");
    }
  }

  return (
    <>
      <Card title="👑 Superadmin panel">
        <p><b>F.I.O:</b> {profile.full_name}</p>
        <p><b>Role:</b> {profile.role}</p>
      </Card>

      {error && (
        <Card title="Xatolik">
          <p className="danger">{error}</p>
        </Card>
      )}

      {stats && (
        <Card title="📊 Umumiy statistika">
          <div className="grid">
            <div><b>{stats.users.total}</b><span>Jami user</span></div>
            <div><b>{stats.users.student}</b><span>Student</span></div>
            <div><b>{stats.users.teacher}</b><span>Teacher</span></div>
            <div><b>{stats.users.admin}</b><span>Admin</span></div>
            <div><b>{stats.groups.active}</b><span>Faol guruh</span></div>
            <div><b>{stats.payments.pending}</b><span>Pending payment</span></div>
          </div>
        </Card>
      )}

      <Card title="👨‍💻 Adminlar">
        {admins.length === 0 ? (
          <p>Adminlar yo‘q.</p>
        ) : (
          admins.map((admin) => (
            <div key={admin.telegram_id} className="resultBox">
              <b>{admin.full_name}</b>
              <p>{admin.role}</p>
            </div>
          ))
        )}
      </Card>

      <Card title="👥 Oxirgi foydalanuvchilar">
        {users.length === 0 ? (
          <p>Userlar yo‘q.</p>
        ) : (
          users.map((user) => (
            <div key={user.telegram_id} className="resultBox">
              <b>{user.full_name || user.telegram_id}</b>
              <p>{user.role}</p>
              <p>{user.phone || "-"}</p>
            </div>
          ))
        )}
      </Card>
    </>
  );
}
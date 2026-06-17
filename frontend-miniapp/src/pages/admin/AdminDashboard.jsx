import { useEffect, useState } from "react";
import Card from "../../components/Card";

export default function AdminDashboard({ api, profile }) {
  const [stats, setStats] = useState(null);
  const [payments, setPayments] = useState([]);
  const [groups, setGroups] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [kicks, setKicks] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    loadAdminData();
  }, []);

  async function loadAdminData() {
    try {
      const statsRes = await api.get("/api/admin/statistics");
      const paymentsRes = await api.get("/api/admin/payments?status=pending");
      const groupsRes = await api.get("/api/admin/groups");
      const teachersRes = await api.get("/api/admin/teachers");
      const kicksRes = await api.get("/api/admin/kick-requests?status=pending");

      setStats(statsRes.data.statistics);
      setPayments(paymentsRes.data.payments || []);
      setGroups(groupsRes.data.groups || []);
      setTeachers(teachersRes.data.teachers || []);
      setKicks(kicksRes.data.kick_requests || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Admin ma'lumotlarini yuklab bo'lmadi.");
    }
  }

  return (
    <>
      <Card title="👨‍💻 Admin panel">
        <p><b>F.I.O:</b> {profile.full_name}</p>
        <p><b>Role:</b> {profile.role}</p>
      </Card>

      {error && (
        <Card title="Xatolik">
          <p className="danger">{error}</p>
        </Card>
      )}

      {stats && (
        <Card title="📊 Statistika">
          <div className="grid">
            <div><b>{stats.students}</b><span>O‘quvchilar</span></div>
            <div><b>{stats.teachers}</b><span>Ustozlar</span></div>
            <div><b>{stats.groups}</b><span>Guruhlar</span></div>
            <div><b>{stats.pending_payments}</b><span>Pending to‘lov</span></div>
          </div>
        </Card>
      )}

      <Card title="💳 Pending to‘lovlar">
        {payments.length === 0 ? (
          <p>Pending to‘lov yo‘q.</p>
        ) : (
          payments.map((payment) => (
            <div key={payment.id} className="resultBox">
              <b>{payment.student_name}</b>
              <p>{payment.course_info}</p>
              <p>{payment.payment_method} — {payment.status}</p>
            </div>
          ))
        )}
      </Card>

      <Card title="📚 Guruhlar">
        {groups.length === 0 ? (
          <p>Guruhlar yo‘q.</p>
        ) : (
          groups.map((group) => (
            <div key={group.id} className="resultBox">
              <b>{group.name}</b>
              <p>Ustoz: {group.teacher_name || "-"}</p>
              <p>{group.current_count}/{group.max_capacity}</p>
            </div>
          ))
        )}
      </Card>

      <Card title="👨‍🏫 Ustozlar">
        {teachers.length === 0 ? (
          <p>Ustozlar yo‘q.</p>
        ) : (
          teachers.map((teacher) => (
            <div key={teacher.telegram_id} className="resultBox">
              <b>{teacher.full_name}</b>
              <p>{teacher.teach_lang || "-"}</p>
            </div>
          ))
        )}
      </Card>

      <Card title="❌ Pending chetlatish so‘rovlari">
        {kicks.length === 0 ? (
          <p>Pending so‘rov yo‘q.</p>
        ) : (
          kicks.map((item) => (
            <div key={item.id} className="resultBox">
              <b>{item.student_name}</b>
              <p>Ustoz: {item.teacher_name}</p>
              <p>Guruh: {item.group_name}</p>
            </div>
          ))
        )}
      </Card>
    </>
  );
}
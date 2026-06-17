import { useEffect, useState } from "react";
import Card from "../../components/Card";

export default function TeacherDashboard({ api, profile }) {
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [students, setStudents] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [results, setResults] = useState([]);
  const [kickRequests, setKickRequests] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    loadTeacherData();
  }, []);

  async function loadTeacherData() {
    try {
      const groupsRes = await api.get("/api/teacher/groups");
      const resultsRes = await api.get("/api/teacher/results");
      const kicksRes = await api.get("/api/teacher/kick-requests");

      setGroups(groupsRes.data.groups || []);
      setResults(resultsRes.data.results || []);
      setKickRequests(kicksRes.data.kick_requests || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Teacher ma'lumotlarini yuklab bo'lmadi.");
    }
  }

  async function openGroup(group) {
    try {
      setSelectedGroup(group);

      const studentsRes = await api.get(`/api/teacher/groups/${group.id}/students`);
      const lessonsRes = await api.get(`/api/teacher/groups/${group.id}/lessons`);

      setStudents(studentsRes.data.students || []);
      setLessons(lessonsRes.data.lessons || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Guruh ma'lumotlarini yuklab bo'lmadi.");
    }
  }

  return (
    <>
      <Card title="👨‍🏫 Ustoz profili">
        <p><b>F.I.O:</b> {profile.full_name}</p>
        <p><b>Fan:</b> {profile.teach_lang || "-"}</p>
        <p><b>Telefon:</b> {profile.phone || "-"}</p>
      </Card>

      {error && (
        <Card title="Xatolik">
          <p className="danger">{error}</p>
        </Card>
      )}

      <Card title="📚 Mening guruhlarim">
        {groups.length === 0 ? (
          <p>Sizga hali guruh biriktirilmagan.</p>
        ) : (
          groups.map((group) => (
            <button key={group.id} className="btn" onClick={() => openGroup(group)}>
              {group.name} — {group.current_count}/{group.max_capacity}
            </button>
          ))
        )}
      </Card>

      {selectedGroup && (
        <>
          <Card title={`👥 O'quvchilar: ${selectedGroup.name}`}>
            {students.length === 0 ? (
              <p>Bu guruhda o‘quvchi yo‘q.</p>
            ) : (
              students.map((student) => (
                <div key={student.telegram_id} className="resultBox">
                  <b>{student.full_name}</b>
                  <p>{student.phone || "-"}</p>
                </div>
              ))
            )}
          </Card>

          <Card title={`🎥 Darslar: ${selectedGroup.name}`}>
            {lessons.length === 0 ? (
              <p>Hali dars yuklanmagan.</p>
            ) : (
              lessons.map((lesson) => (
                <div key={lesson.id} className="lessonBox">
                  <b>{lesson.title}</b>
                  <p>{lesson.material_type || "material"}</p>
                  {lesson.material_url && (
                    <a className="fileLink" href={lesson.material_url} target="_blank">
                      Faylni ochish
                    </a>
                  )}
                </div>
              ))
            )}
          </Card>
        </>
      )}

      <Card title="📊 Kiritilgan natijalar">
        {results.length === 0 ? (
          <p>Hali natija kiritilmagan.</p>
        ) : (
          results.slice(0, 10).map((result) => (
            <div key={result.id} className="resultBox">
              <b>{result.student_name}</b>
              <p>{result.result_title}: {result.score}</p>
              <p>{result.group_name}</p>
            </div>
          ))
        )}
      </Card>

      <Card title="❌ Chetlatish so‘rovlari">
        {kickRequests.length === 0 ? (
          <p>Hali so‘rov yo‘q.</p>
        ) : (
          kickRequests.slice(0, 10).map((item) => (
            <div key={item.id} className="resultBox">
              <b>{item.student_name}</b>
              <p>{item.group_name}</p>
              <p>Status: {item.status}</p>
            </div>
          ))
        )}
      </Card>
    </>
  );
}
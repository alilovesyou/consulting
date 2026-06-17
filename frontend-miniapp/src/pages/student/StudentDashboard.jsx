import { useEffect, useState } from "react";
import Card from "../../components/Card";

export default function StudentDashboard({ api, profile }) {
  const [groups, setGroups] = useState([]);
  const [results, setResults] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    loadStudentData();
  }, []);

  async function loadStudentData() {
    try {
      const groupsRes = await api.get("/api/student/groups");
      const resultsRes = await api.get("/api/student/results");

      setGroups(groupsRes.data.groups || []);
      setResults(resultsRes.data.results || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Student ma'lumotlarini yuklab bo'lmadi.");
    }
  }

  async function openGroup(group) {
    try {
      setSelectedGroup(group);
      setLessons([]);

      const res = await api.get(`/api/student/groups/${group.id}/lessons`);
      setLessons(res.data.lessons || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Darslarni yuklab bo'lmadi.");
    }
  }

  return (
    <>
      <Card title="👤 Profil">
        <p><b>F.I.O:</b> {profile.full_name}</p>
        <p><b>Telefon:</b> {profile.phone || "-"}</p>
        <p><b>Hudud:</b> {profile.region || "-"}</p>
      </Card>

      {error && (
        <Card title="Xatolik">
          <p className="danger">{error}</p>
        </Card>
      )}

      <Card title="📚 Guruhlarim">
        {groups.length === 0 ? (
          <p>Siz hali hech qaysi guruhga qo‘shilmagansiz.</p>
        ) : (
          groups.map((group) => (
            <button
              key={group.id}
              className="btn"
              onClick={() => openGroup(group)}
            >
              {group.name} — {group.language}
            </button>
          ))
        )}
      </Card>

      {selectedGroup && (
        <Card title={`🎥 Darslar: ${selectedGroup.name}`}>
          {lessons.length === 0 ? (
            <p>Bu guruhda hali dars yuklanmagan.</p>
          ) : (
            lessons.map((lesson) => (
              <div key={lesson.id} className="lessonBox">
                <h3>{lesson.title}</h3>

                {lesson.material_type === "video" && lesson.material_url && (
                  <video controls className="media">
                    <source src={lesson.material_url} />
                  </video>
                )}

                {lesson.material_type === "photo" && lesson.material_url && (
                  <img src={lesson.material_url} alt={lesson.title} className="media" />
                )}

                {lesson.material_type === "document" && lesson.material_url && (
                  <a className="fileLink" href={lesson.material_url} target="_blank">
                    📄 Faylni ochish
                  </a>
                )}
              </div>
            ))
          )}
        </Card>
      )}

      <Card title="📊 Natijalarim">
        {results.length === 0 ? (
          <p>Hali natija kiritilmagan.</p>
        ) : (
          results.map((result) => (
            <div key={result.id} className="resultBox">
              <b>{result.result_title}</b>
              <p>Ball: {result.score}</p>
              <p>Guruh: {result.group_name}</p>
              {result.comment && <p>Izoh: {result.comment}</p>}
            </div>
          ))
        )}
      </Card>
    </>
  );
}
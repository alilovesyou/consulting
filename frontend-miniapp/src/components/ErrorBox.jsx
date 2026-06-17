export default function ErrorBox({ message }) {
  return (
    <div className="page">
      <section className="card error">
        <h2>Xatolik</h2>
        <p>{message}</p>
        <p className="muted">
          Mini App Telegram ichida ochilganda initData avtomatik keladi.
        </p>
      </section>
    </div>
  );
}
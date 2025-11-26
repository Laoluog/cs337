export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-screen flex flex-col items-center p-5">
      <div className="w-full max-w-5xl">{children}</div>
    </main>
  );
}

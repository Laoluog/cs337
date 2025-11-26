import { HomeLanding } from "@/components/brain/home-landing";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center p-5">
      <div className="w-full max-w-5xl">
        <HomeLanding />
      </div>
    </main>
  );
}

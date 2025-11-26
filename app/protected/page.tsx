export default function ProtectedPage() {
  return (
    <div className="flex-1 w-full flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Workspace</h1>
      <ul className="list-disc pl-6">
        <li>
          <a className="underline" href="/protected/brain/cases">
            View all cases
          </a>
        </li>
        <li>
          <a className="underline" href="/protected/brain/input">
            Create a new case
          </a>
        </li>
      </ul>
    </div>
  );
}

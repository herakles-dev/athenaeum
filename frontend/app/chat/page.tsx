import ChatInterface from "@/components/ChatInterface";

export const metadata = { title: "Chat — Alan Watts Library" };

export default function ChatPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">AI Alan Watts Librarian</h1>
        <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>
          Responses grounded in 238 actual lectures and essays via semantic search.
        </p>
      </div>
      <ChatInterface />
    </div>
  );
}

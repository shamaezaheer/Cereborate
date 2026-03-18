const WS_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, "ws") || "ws://localhost:8000";

export type WSMessage =
  | { type: "message"; content: string; extracted: Record<string, unknown>; is_complete: boolean }
  | { type: "error"; message: string }
  | { type: "pong" };

export class PlanningWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private token: string;
  private onMessage: (msg: WSMessage) => void;
  private onClose: () => void;

  constructor(
    sessionId: string,
    token: string,
    onMessage: (msg: WSMessage) => void,
    onClose: () => void
  ) {
    this.sessionId = sessionId;
    this.token = token;
    this.onMessage = onMessage;
    this.onClose = onClose;
  }

  connect() {
    const url = `${WS_URL}/api/v1/ws/plan/${this.sessionId}?token=${this.token}`;
    this.ws = new WebSocket(url);

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        this.onMessage(msg);
      } catch {}
    };

    this.ws.onclose = () => this.onClose();
  }

  send(content: string) {
    this.ws?.send(JSON.stringify({ type: "message", content }));
  }

  disconnect() {
    this.ws?.close();
  }
}

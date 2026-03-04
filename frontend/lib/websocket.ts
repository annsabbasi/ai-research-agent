import type { WSMessage } from "@/types";

export class ResearchWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private onMessage: (msg: WSMessage) => void;
  private onClose?: () => void;

  constructor(
    queryId: number,
    onMessage: (msg: WSMessage) => void,
    onClose?: () => void
  ) {
    const wsUrl =
      process.env.NEXT_PUBLIC_WS_URL || "ws://localhost/ws";
    const token = localStorage.getItem("access_token");
    this.url = `${wsUrl}/research/${queryId}/?token=${token}`;
    this.onMessage = onMessage;
    this.onClose = onClose;
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onmessage = (event) => {
      const data: WSMessage = JSON.parse(event.data);
      this.onMessage(data);
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = Math.pow(2, this.reconnectAttempts) * 1000;
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), delay);
      } else {
        this.onClose?.();
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect() {
    this.maxReconnectAttempts = 0;
    this.ws?.close();
  }
}

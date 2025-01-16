import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ChatHistoryService {

  private history: { id: number; messages: { text: string; sender: string }[] }[] = [];
  private currentChatId: number | null = null;

  constructor() { }

  startNewConversation() {
    const newChat = { id: this.history.length + 1, messages: [] };
    this.history.push(newChat);
    this.currentChatId = newChat.id;
  }

  addMessageToCurrentChat(message: { text: string; sender: string }) {
    if (this.currentChatId !== null) {
      const chat = this.history.find((c) => c.id === this.currentChatId);
      if (chat && !chat.messages.includes(message)) {
        chat.messages.push(message);
      }
    }
  }

  getAllConversations() {
    return this.history;
  }

  getMessagesByChatId(chatId: number) {
    const chat = this.history.find((c) => c.id === chatId);
    return chat ? chat.messages : [];
  }

  setCurrentChat(chatId: number) {
    this.currentChatId = chatId;
  }

  getCurrentChatId() {
    return this.currentChatId;
  }
}

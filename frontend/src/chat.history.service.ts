import { Injectable } from '@angular/core';
import {environment} from './app/app.config';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ChatHistoryService {

  private history: { id: number; messages: { text: string; sender: string }[] }[] = [];
  private currentChatId: number | null = null;

  constructor(private http: HttpClient) {}

  startNewConversation() {
    const newChat = { id: this.history.length + 1, messages: [] };
    this.history.push(newChat);
    this.currentChatId = newChat.id;

    this.http.post(`${environment.apiUrl}/startNewChatSession`, {}).subscribe({
      next: (response: any) => {
        console.log('New chat session started:', response);
      },
      error: (error) => {
        console.error('Failed to start a new chat session:', error);
      },
    });
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

    this.http.post(`${environment.apiUrl}/updateCurrentChatSession?chat_id=${chatId}`, {}).subscribe({
      next: (response: any) => {
        console.log('Current chat session updated in backend:', response);
      },
      error: (error) => {
        console.error('Failed to update current chat session in backend:', error);
      },
    });
  }

  getCurrentChatId() {
    return this.currentChatId;
  }
}

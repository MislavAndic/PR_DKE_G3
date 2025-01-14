import {Component, OnInit} from '@angular/core';
import {NgClass, NgForOf} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import { environment } from '../app.config';
import {ChatHistoryService} from '../../chat.history.service';


@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  standalone: true,
  imports: [
    NgForOf,
    NgClass,
    FormsModule
  ],
  styleUrls: ['./chat.component.css']
})

export class ChatComponent implements OnInit {
  messages: { sender: string, text: string }[] = [];
  userInput: string = '';
  allConversations: { id: number, messages: { sender: string, text: string }[] }[] = [];

  constructor(private http: HttpClient, private chatHistoryService: ChatHistoryService) {}

  ngOnInit() {
    const currentChatId = this.chatHistoryService.getCurrentChatId();
    if (currentChatId !== null) {
      this.messages = this.chatHistoryService.getMessagesByChatId(currentChatId);
    } else {
      this.chatHistoryService.startNewConversation();
      const welcomeMessage = {
        text: 'Hallo ich bin dein persönlicher Helfer bei Fragen zu den Arbeitsmarktdaten 2024. Wie kann ich dir weiterhelfen?',
        sender: 'bot'
      };
      this.messages.push(welcomeMessage);
      this.chatHistoryService.addMessageToCurrentChat(welcomeMessage);
    }
    this.allConversations = this.chatHistoryService.getAllConversations();
  }


  resetChat() {
    this.chatHistoryService.startNewConversation();
    this.messages = [];
    this.messages.push({
      text: 'Hallo, ich bin dein persönlicher Helfer bei Fragen zu Arbeitsmarktdaten 2024. Wie kann ich dir helfen?',
      sender: 'bot'
    });
    this.allConversations = this.chatHistoryService.getAllConversations();
  }

  sendMessage() {
    if (this.userInput.trim()) {
      const userMessage = { sender: 'user', text: this.userInput };
      this.messages.push(userMessage);
      this.chatHistoryService.addMessageToCurrentChat(userMessage);

      this.getBotResponse(this.userInput);

      this.userInput = '';
    }
  }

  getBotResponse(userMessage: string) {
    this.http.post<any>(environment.apiUrl, { prompt: userMessage }, {headers: new HttpHeaders({'Access-Control-Allow-Origin':'*'})})
      .subscribe({
        next: (response) => {
          const botReply = response.response || "Bot antwortet gerade nicht";
          const botMessage = { sender: 'bot', text: botReply };

          this.messages.push(botMessage);
          this.chatHistoryService.addMessageToCurrentChat(botMessage);
        },

        error: (error) => {
          console.error('Fehler beim Abrufen der Bot-Antwort:', error);
          const botReply = "REALLY NOT FEELING UP TO IT RIGHT NOW. SORRY.";
          const botMessage = { sender: 'bot', text: botReply };

          this.messages.push(botMessage);
          this.chatHistoryService.addMessageToCurrentChat(botMessage);
        },

        complete: () => {
          console.log("Request is completed");
        }
      });
  }

  continueConversation(chatId: number) {
    this.messages = [];
    this.chatHistoryService.setCurrentChat(chatId);
    this.messages = this.chatHistoryService.getMessagesByChatId(chatId);
  }
}

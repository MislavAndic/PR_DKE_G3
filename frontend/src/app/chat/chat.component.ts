import { Component } from '@angular/core';
import {NgClass, NgForOf} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import { environment } from '../app.config';

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
export class ChatComponent {
  messages: { sender: string, text: string }[] = [];
  userInput: string = '';

  constructor(private http: HttpClient) {}

  sendMessage() {
    if (this.userInput.trim()) {
      this.messages.push({ sender: 'user', text: this.userInput });

      this.getBotResponse(this.userInput);

      this.userInput = '';
    }
  }

  getBotResponse(userMessage: string) {
    this.http.post<any>(environment.apiUrl, { prompt: userMessage }, {headers: new HttpHeaders({'Access-Control-Allow-Origin':'*'})})
      .subscribe(response => {
          const botReply = response.response || "Bot antwortet gerade nicht";
          this.messages.push({ sender: 'bot', text: botReply });
        },
        error => {
          console.error('Fehler beim Abrufen der Bot-Antwort:', error);
          const botReply = "REALLY NOT FEELING UP TO IT RIGHT NOW. SORRY.";
          this.messages.push({ sender: 'bot', text: botReply });
        }
      );
  }
}

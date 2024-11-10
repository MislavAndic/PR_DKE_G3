import { Component } from '@angular/core';
import {NgClass, NgForOf} from '@angular/common';
import {FormsModule} from '@angular/forms';

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

  sendMessage() {
    if (this.userInput.trim()) {
      this.messages.push({ sender: 'user', text: this.userInput });

      this.getBotResponse(this.userInput);

      this.userInput = '';
    }
  }

  getBotResponse(userMessage: string) {
    // Hier könnte ein HTTP-Aufruf an eine Chatbot-API erfolgen
    setTimeout(() => {
      const botReply = `REALLY NOT FEELING UP TO IT RIGHT NOW. SORRY.`;
      this.messages.push({ sender: 'bot', text: botReply });
    }, 1000);
  }
}

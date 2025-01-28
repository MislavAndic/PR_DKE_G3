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

  sendPretypedMessage(event : Event) {
    const button = event.target as HTMLButtonElement;
    const buttonText = button.innerText;
    this.userInput = buttonText; // Prepopulate the user input for clarity
    this.sendMessage(); // Use the existing sendMessage method
  }

  getBotResponse(userMessage: string) {
    const botMessage = { sender: 'bot', text: '' }; // For streaming updates
    this.messages.push(botMessage);

    // Use fetch to handle streaming response
    fetch(`${environment.apiUrl}/queryLlm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: userMessage })
    })
      .then(async (response) => {
        const reader = response.body?.getReader();
        const decoder = new TextDecoder('utf-8');
        let done = false;

        while (!done) {
          const { value, done: readerDone } = await reader?.read() || {};
          done = readerDone || false;
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            console.log("Received chunk:", chunk);
            botMessage.text += chunk; // Append streamed text chunk to message
          }
        }
      })
      .catch((error) => {
        console.error('Error while streaming response:', error);
        botMessage.text = "REALLY NOT FEELING UP TO IT RIGHT NOW SORRY";
      })
      .finally(() => {
        this.chatHistoryService.addMessageToCurrentChat(botMessage);
      });
  }

  continueConversation(chatId: number) {
    this.messages = [];
    this.chatHistoryService.setCurrentChat(chatId);
    this.messages = this.chatHistoryService.getMessagesByChatId(chatId);
  }
}

import React, { useState } from 'react';
import '../styles/message.css';

interface MessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  };
  showAvatar?: boolean;
}

// Simple markdown parser for common formatting
const parseMarkdown = (text: string) => {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Headers
    if (line.startsWith('# ')) {
      elements.push(<h1 key={i}>{line.substring(2)}</h1>);
    } else if (line.startsWith('## ')) {
      elements.push(<h2 key={i}>{line.substring(3)}</h2>);
    } else if (line.startsWith('### ')) {
      elements.push(<h3 key={i}>{line.substring(4)}</h3>);
    }
    // Bold and italic
    else if (line.includes('**') || line.includes('*')) {
      const formatted = line
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
      elements.push(
        <p key={i} dangerouslySetInnerHTML={{ __html: formatted }} />
      );
    }
    // Lists
    else if (line.startsWith('- ')) {
      const listItems: string[] = [];
      while (i < lines.length && lines[i].startsWith('- ')) {
        listItems.push(lines[i].substring(2));
        i++;
      }
      elements.push(
        <ul key={i}>
          {listItems.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      );
      i--;
    }
    // Code blocks
    else if (line.startsWith('```')) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      elements.push(
        <pre key={i}>
          <code>{codeLines.join('\n')}</code>
        </pre>
      );
    }
    // Regular paragraphs
    else if (line.trim()) {
      elements.push(<p key={i}>{line}</p>);
    } else {
      elements.push(<br key={i} />);
    }

    i++;
  }

  return elements;
};

export const Message: React.FC<MessageProps> = ({ message, showAvatar = true }) => {
  const [isHovered, setIsHovered] = useState(false);

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '';
    }
  };

  const formattedTime = formatTime(message.timestamp);
  const isUser = message.role === 'user';
  const avatarContent = isUser ? '👤' : '🤖';

  return (
    <div
      className={`message-wrapper ${isUser ? 'user-wrapper' : 'assistant-wrapper'}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {showAvatar && !isUser && <div className="avatar">{avatarContent}</div>}

      <div className="message-container">
        <div
          className={`bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}
          role="listitem"
          aria-label={`${isUser ? 'User' : 'Assistant'} message at ${formattedTime}`}
        >
          <div className="message-content">
            {isUser ? message.content : parseMarkdown(message.content)}
          </div>
          <div
            className={`timestamp ${isHovered ? 'timestamp-visible' : ''}`}
            aria-hidden="true"
          >
            {formattedTime}
          </div>
        </div>

        {showAvatar && isUser && <div className="avatar">{avatarContent}</div>}
      </div>
    </div>
  );
};
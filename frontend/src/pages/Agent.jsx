import { useState, useRef, useEffect } from 'react';
import api from '../api/client';

export default function Agent() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Olá! Sou seu Assistente Financeiro IA. 🤖\nPosso analisar seus gastos ou registrar novas despesas para você. Exemplo: "Gastei R$ 45 de Uber hoje" ou "Adicione uma despesa de R$ 120 no supermercado ontem".\n\n📸 **Novidade:** Você também pode anexar a foto de um cupom fiscal e eu leio tudo para você!'
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const endRef = useRef(null);
  const fileInputRef = useRef(null);

  // Voice Recognition Logic
  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Seu navegador não suporta reconhecimento de voz.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    
    recognition.onerror = (event) => {
      console.error('Speech Recognition Error', event.error);
      setIsListening(false);
      if (event.error === 'not-allowed') {
        alert("Acesso ao microfone negado. Por favor, permita o acesso nas configurações do seu navegador.");
      } else if (event.error === 'no-speech') {
        // Just stop quietly if no speech detected
      } else {
        alert("Erro no reconhecimento de voz: " + event.error);
      }
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      // Auto-send after a small delay to let user see the text
      setTimeout(() => {
        sendMessage(transcript);
      }, 800);
    };

    try {
      recognition.start();
    } catch (e) {
      console.error(e);
      setIsListening(false);
    }
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, selectedImage]);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onloadend = () => {
      setSelectedImage(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const sendMessage = async (presetText = null) => {
    const text = presetText || input;
    if (!text.trim() && !selectedImage) return;

    // Create message for UI
    const userMsgContent = [];
    if (text) userMsgContent.push(text);
    if (selectedImage) userMsgContent.push("[Imagem Anexada]");

    const newMsgs = [...messages, { role: 'user', content: userMsgContent.join('\n') }];
    setMessages(newMsgs);
    
    const payload = { 
        question: text || "Aqui está um comprovante/cupom.", 
        image_base64: selectedImage 
    };

    setInput('');
    setSelectedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setLoading(true);

    try {
      const res = await api.post('/api/chat', payload);
      setMessages([...newMsgs, { role: 'assistant', content: res.data.answer }]);
    } catch (err) {
      setMessages([...newMsgs, { role: 'assistant', content: 'Desculpe, ocorreu um erro ao processar sua solicitação ou a imagem.' }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "Gastei R$ 50 no Ifood hoje",
    "Fiz uma compra de R$ 120 no supermercado ontem",
    "Como posso economizar?",
    "Resuma meus gastos deste mês"
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 60px)', maxWidth: '800px', margin: '0 auto' }}>
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <div>
            <h1>🤖 Assistente IA</h1>
            <p>Converse com a inteligência artificial para gerenciar suas finanças e ler cupons fiscais.</p>
          </div>
          <button 
            className="btn btn-secondary btn-sm" 
            onClick={async () => {
              setLoading(true);
              try {
                const res = await api.post('/api/agent/trigger');
                alert(res.data.alert ? 'Dica Gerada! Verifique o sininho 🔔' : 'A IA analisou seus dados e achou que está tudo ok por enquanto.');
              } catch(e) { alert('Erro ao disparar motor.'); }
              setLoading(false);
            }}
            disabled={loading}
          >
            ⚡ Testar Motor Proativo
          </button>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', background: 'var(--bg-elevated)', borderRadius: '12px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid var(--border)' }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '80%',
              padding: '12px 16px',
              borderRadius: '16px',
              borderBottomRightRadius: m.role === 'user' ? 0 : '16px',
              borderBottomLeftRadius: m.role === 'assistant' ? 0 : '16px',
              background: m.role === 'user' ? 'var(--accent)' : 'var(--bg-base)',
              color: m.role === 'user' ? '#fff' : 'var(--text)',
              border: m.role === 'assistant' ? '1px solid var(--border)' : 'none',
              lineHeight: 1.5,
              whiteSpace: 'pre-wrap'
            }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ padding: '12px 16px', borderRadius: '16px', background: 'var(--bg-base)', border: '1px solid var(--border)' }}>
              <div className="spinner" style={{ width: '16px', height: '16px', borderTopColor: 'var(--accent)' }} />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div style={{ marginTop: '16px' }}>
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '8px', marginBottom: '8px' }}>
          {suggestions.map((s, i) => (
            <button key={i} className="btn btn-secondary btn-sm" style={{ whiteSpace: 'nowrap', borderRadius: '20px' }} onClick={() => sendMessage(s)}>
              {s}
            </button>
          ))}
        </div>

        {selectedImage && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, padding: 8, background: 'var(--bg-elevated)', borderRadius: 8, width: 'fit-content' }}>
                <img src={selectedImage} alt="Preview" style={{ height: 40, borderRadius: 4 }} />
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Imagem pronta para envio</span>
                <button className="btn btn-sm" style={{ padding: '2px 8px' }} onClick={() => { setSelectedImage(null); fileInputRef.current.value=''; }}>❌</button>
            </div>
        )}

        <div style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="file" 
            accept="image/*" 
            style={{ display: 'none' }} 
            ref={fileInputRef} 
            onChange={handleImageChange}
          />
          <button 
            className="btn btn-secondary" 
            style={{ borderRadius: '24px', padding: '0 16px', fontSize: 20 }} 
            onClick={() => fileInputRef.current?.click()}
            title="Anexar Cupom Fiscal"
          >
            📸
          </button>

          <button 
            className={`btn ${isListening ? 'btn-danger pulse' : 'btn-secondary'}`} 
            style={{ borderRadius: '24px', padding: '0 16px', fontSize: 20, transition: 'all 0.3s' }} 
            onClick={startListening}
            title="Comando de Voz"
            disabled={loading}
          >
            {isListening ? '🛑' : '🎙️'}
          </button>
          
          <input 
            className="form-control" 
            style={{ flex: 1, borderRadius: '24px', padding: '0 20px' }}
            value={input} 
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder="Digite sua mensagem ou anexe um cupom fiscal..." 
            disabled={loading}
          />
          <button className="btn btn-primary" style={{ borderRadius: '24px', padding: '0 24px' }} onClick={() => sendMessage()} disabled={loading || (!input.trim() && !selectedImage)}>
            Enviar
          </button>
        </div>
      </div>
    </div>
  );
}

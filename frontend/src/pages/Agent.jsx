import { useState, useRef, useEffect } from 'react';
import api from '../api/client';
import { useToast } from '../contexts/ToastContext';

export default function Agent() {
  const toast = useToast()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Olá! Sou seu Assistente Financeiro IA. 🤖\nPosso analisar seus gastos ou registrar novas despesas para você. Exemplo: "Gastei R$ 45 de Uber hoje" ou "Adicione uma despesa de R$ 120 no supermercado ontem".\n\n📸 **Novidade:** Você também pode anexar a foto de um cupom fiscal e eu leio tudo para você!'
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const endRef = useRef(null);
  const fileInputRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = () => {
          const base64Audio = reader.result;
          sendAudioMessage(base64Audio);
        };
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (err) {
      console.error(err);
      toast.error('Erro ao acessar microfone. Verifique as permissões do seu navegador.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const sendAudioMessage = async (base64Audio) => {
    const newMsgs = [...messages, { role: 'user', content: '[Mensagem de Voz 🎙️]' }];
    setMessages(newMsgs);
    setLoading(true);

    try {
      const res = await api.post('/api/chat', { 
        question: "O usuário enviou um áudio.", 
        audio_base64: base64Audio 
      });
      setMessages([...newMsgs, { role: 'assistant', content: res.data.answer }]);
    } catch (err) {
      setMessages([...newMsgs, { role: 'assistant', content: 'Erro ao processar áudio. Tente novamente.' }]);
    } finally {
      setLoading(false);
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
        question: text || "Aqui está um comprovante/cupom."
    };
    if (selectedImage) payload.image_base64 = selectedImage;

    setInput('');
    setSelectedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setLoading(true);

    try {
      const res = await api.post('/api/chat', payload);
      setMessages([...newMsgs, { role: 'assistant', content: res.data.answer }]);
    } catch (err) {
      console.error("Chat Error:", err);
      const errDetail = err.response?.data?.detail || err.response?.status || err.message;
      setMessages([...newMsgs, { role: 'assistant', content: `Desculpe, ocorreu um erro: ${errDetail}` }]);
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
    <div className="agent-container">
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
                if (res.data.alert) {
                  toast.info('💡 Dica gerada! Verifique o sininho 🔔');
                } else {
                  toast.success('A IA analisou seus dados e está tudo bem!');
                }
              } catch(e) {
                toast.error('Erro ao disparar motor proativo.');
              }
              setLoading(false);
            }}
            disabled={loading}
          >
            ⚡ Testar Motor Proativo
          </button>
        </div>
      </div>

      <div className="chat-messages">
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
        <div className="suggestions-bar">
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
            capture="environment"
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
            className={`btn ${isRecording ? 'btn-danger pulse' : 'btn-secondary'}`} 
            style={{ 
                borderRadius: '24px', 
                padding: '0 16px', 
                fontSize: 20, 
                transition: 'all 0.3s',
                boxShadow: isRecording ? '0 0 15px var(--danger)' : 'none'
            }} 
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
            title="Segure para falar"
            disabled={loading}
          >
            {isRecording ? '🛑' : '🎙️'}
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

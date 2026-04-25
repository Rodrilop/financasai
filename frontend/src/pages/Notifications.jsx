import { useEffect, useState } from 'react';
import api from '../api/client';

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/api/notifications');
      setNotifications(res.data);
    } catch (err) {
      console.error('Erro ao carregar notificações', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const markAsRead = async (id) => {
    try {
      await api.put(`/api/notifications/${id}/read`);
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error(err);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR') + ' às ' + date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div>
      <div className="page-header">
        <h1>🔔 Notificações da IA</h1>
        <p>Alertas e dicas gerados automaticamente pelo seu consultor proativo.</p>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {notifications.length === 0 ? (
            <div className="chart-card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              Nenhuma notificação por enquanto. O Agente IA avisará você quando houver algo importante!
            </div>
          ) : (
            notifications.map(n => (
              <div 
                key={n.id} 
                className="chart-card" 
                style={{ 
                  borderLeft: n.is_read ? '1px solid var(--border)' : '4px solid var(--accent)',
                  opacity: n.is_read ? 0.8 : 1,
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '16px', color: n.is_read ? 'var(--text)' : 'var(--accent)' }}>{n.title}</h3>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{formatDate(n.created_at)}</span>
                </div>
                <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.5' }}>{n.message}</p>
                {!n.is_read && (
                  <button 
                    onClick={() => markAsRead(n.id)}
                    style={{ 
                      marginTop: '12px', 
                      background: 'none', 
                      border: 'none', 
                      color: 'var(--accent)', 
                      cursor: 'pointer', 
                      fontSize: '12px', 
                      padding: 0,
                      textDecoration: 'underline'
                    }}
                  >
                    Marcar como lida
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

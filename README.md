# 💪 GymApp — Aplicativo de Treino e Gestão Fitness

![GymApp](https://img.shields.io/badge/GymApp-v1.0-brightgreen?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-FastAPI-blue?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react)
![MongoDB](https://img.shields.io/badge/MongoDB-Database-47A248?style=for-the-badge&logo=mongodb)

---

## 📌 Sobre o Projeto

O **GymApp** é uma plataforma Full Stack de gestão para academias, desenvolvida para centralizar e automatizar o controle de alunos, treinos, planos e financeiro em um único lugar.

O sistema foi pensado para funcionar como uma ferramenta real de gestão — similar a apps de grandes redes como SmartFit — porém com foco em academias independentes que precisam de controle operacional sem complexidade desnecessária.

> 🔄 O projeto está em **evolução contínua**. Novas funcionalidades são adicionadas com frequência.

---

## 🚀 Demonstração

Acesse a aplicação em funcionamento pelo link abaixo:

🔗 **[https://gymappdem.netlify.app](https://gymappdem.netlify.app)**

### ⚠️ Ambiente de Demonstração

Esta versão está hospedada em ambiente gratuito (Render + Netlify).  
Caso o sistema esteja inativo por um período, o backend pode levar **até 50 segundos** para responder na primeira requisição — isso é normal no plano gratuito do Render.

---

## 🔐 Credenciais de Teste

| Perfil | Email | Senha |
|--------|-------|-------|
| 👑 Admin   | EMAIL: `admin@gymapp.com` | SENHA: `admin123` |
| 🏋️ Aluno 1 | EMAIL: `aluno.428720@gymmanager.com` | SENHA: `bomdia248` |
| 🏋️ Aluno 2 | EMAIL: `aluno.00ce03@gymmanager.com` | SENHA: `bomdia248` |

> ⚠️ Ambiente de demonstração — os dados podem ser alterados ou resetados a qualquer momento.

---

## 📱 Funcionalidades

### 👑 Painel Administrativo
- Dashboard com métricas em tempo real (alunos ativos, inadimplentes, treinos, check-ins)
- Gerenciamento completo de alunos (criar, editar, excluir, resetar senha)
- Criação e atribuição de treinos personalizados
- Criação de planos de treino (ex: Hipertrofia, MR Olympia, etc.)
- Controle financeiro com status de pagamento por aluno
- Relatório financeiro com gráficos de distribuição por plano e status

### 🏋️ Área do Aluno
- 📋 **Acesso ao treino personalizado** atribuído pelo administrador  
- ⏱️ **Cronômetro integrado** para controle de descanso entre séries
- ✅ **Registro de treinos concluídos** com marcação em tempo real  
- 📊 **Histórico de atividades** para acompanhamento de evolução  
- 🏆 **Sistema de ranking gamificado** com XP e patentes, baseado na consistência semanal (inspirado em sistemas como Duolingo — ranking global e pessoal)

---

## 🛠️ Tecnologias Utilizadas

### 🔹 Front-end
- React (CRA)
- Tailwind CSS
- Recharts (gráficos)
- Axios

### 🔹 Back-end
- Python
- FastAPI
- Uvicorn / Gunicorn
- SlowAPI (rate limiting)
- Python-Jose (JWT)
- Bcrypt (hashing de senhas)

### 🔹 Banco de Dados
- MongoDB Atlas
- Motor (driver async para MongoDB)

### 🔹 Infraestrutura
- Frontend: **Netlify**
- Backend: **Render**
- Banco: **MongoDB Atlas**

---

## 🧠 Arquitetura do Sistema

```
gymappdem.netlify.app  →  React Frontend
        ↓
gymapp-e44z.onrender.com  →  FastAPI Backend
        ↓
MongoDB Atlas  →  Banco de Dados
```

O projeto segue arquitetura Full Stack com separação clara entre:
- Interface do usuário (React + Tailwind)
- Camada de regras de negócio (FastAPI + JWT)
- Persistência de dados (MongoDB Atlas)

---

## 🔐 Segurança

- Autenticação via **JWT** com expiração configurável
- Senhas hasheadas com **bcrypt**
- Rate limiting no endpoint de login (5 tentativas/minuto)
- Separação de roles: `admin` e `aluno`
- CORS configurado por variável de ambiente

---

## 🗂️ Estrutura do Projeto

```
GymApp/
├── gym-frontend/          # React App
│   ├── src/
│   └── ...
│
└── gym-backend/           # FastAPI App
    ├── app/
    │   ├── core/          # config.py, security.py
    │   ├── models/
    │   ├── routes/        # auth, admin, alunos, treinos, financeiro...
    │   ├── schemas/
    │   └── services/      # database.py
    ├── requirements.txt
    ├── render.yaml
    └── Procfile
```

---

## ⚙️ Como Rodar Localmente

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- MongoDB Atlas (ou local)

### Backend

```bash
cd gym-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Crie um `.env` baseado no `.env.example`:

```env
MONGO_URI=sua_uri_do_mongo
SECRET_KEY=sua_chave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
CORS_ORIGINS=http://localhost:5173
```

Inicie o servidor:

```bash
uvicorn app.main:app --reload
```

Acesse a documentação: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend

```bash
cd gym-frontend
npm install
npm run dev
```

---

## 🚀 Possibilidades de Expansão

- [ ] Notificações automáticas via WhatsApp
- [ ] Sistema de check-in por QR Code
- [ ] Integração com pagamentos online
- [ ] App mobile (React Native)
- [ ] Dashboard com métricas avançadas
- [ ] Sistema multi-unidades
- [ ] Avaliação física integrada
- [ ] Notificações de vencimento de plano

---

## ⚠️ Status do Projeto

O projeto está **funcional e em produção**, mas ainda em desenvolvimento ativo. Algumas áreas em maturação:

- **Testes automatizados**: ainda sendo estruturados
- **Novas features**: sendo desenvolvidas continuamente
- **Performance**: otimizações planejadas para versões futuras

---

## 🏢 Aplicação Comercial

O GymApp foi desenvolvido como **produto base replicável**, podendo ser adaptado para:

- Academias independentes
- Estúdios de musculação
- Boxes de CrossFit
- Personal trainers
- Qualquer negócio que precise de controle de alunos e treinos

A estrutura permite personalização completa de identidade visual, serviços e planos.

---

## 👨‍💻 Desenvolvido por DevDavid

Full Stack Developer focado em criação de soluções reais, com visão de produto e aplicação comercial.

## 📬 Contato

- 📧 **Email:** [devdavidnakahara@gmail.com](mailto:devdavidnakahara@gmail.com)  
- 💼 **LinkedIn:** [David Nakahara](https://www.linkedin.com/in/david-nakahara-8a5132320/)

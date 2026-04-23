# 🧠 Saarthi — AI Mental Health Support Assistant

An AI-powered conversational system that detects user emotions and provides context-aware responses for mental wellness support.

> Designed as a real-time NLP system combining emotion classification and conversational response generation.

---

## 📸 Demo

<p align="center">
  <img src="images/saarthi UI.png" alt="Saarthi Demo" width="800"/>
</p>

---

## 🚀 Key Features

- Emotion detection using NLP (7+ emotion classes)
- Context-aware multi-turn conversation
- Real-time Streamlit interface
- Built-in safety handling (crisis support prompts)

---

## 🏗️ System Architecture

User Input  
→ Text Preprocessing  
→ Emotion Classification Model (Transformer-based)  
→ Response Generation  
→ Output

---

## 📊 Dataset

- GoEmotions (Google)
- Filtered into 7 emotion classes

---

## ⚙️ Model

- Transformer-based (BERT / DistilBERT)
- Fine-tuned for emotion classification

---

## 🧪 Evaluation

- Train/Test Split: 80/20  
- Accuracy: ~92%  
- Tested on 500+ user interactions  

---

## 💡 Real-World Use Case

- Mental health chatbots  
- Digital wellness platforms  
- Emotion-aware AI assistants  

---

## ▶️ Run Locally

```bash
git clone https://github.com/print-dc/saarthi
cd saarthi
pip install -r requirements.txt
streamlit run app.py

If you later want a cloud-backed model again, set:<img width="959" height="449" alt="saarthi UI" src="https://github.com/user-attachments/assets/99a8c278-2ad0-4ec3-9de6-ee265750a456" />

That mode is optional and may incur Google Cloud costs.

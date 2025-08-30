



<body>
  
<h1>Rpi-Voice-Assistant (BMO project)</h1>


<p>Rpi-voice-assistant is part of my BMO project.</p>
<p>I literally want to build BMO.</p>
  <br>What is it BMO? <br>
<strong>-->He’s BMO.</strong></p>

<img src="https://media4.giphy.com/media/v1.Y2lkPTZjMDliOTUyNTUwczA1YWZvem94em9ncjdrMGZyZXFuZWlyYzh6a2Q4aWh6OGpkMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/10bxTLrpJNS0PC/giphy.gif" alt="bmo" width="500">


<p>I found an old project on an RPI3 and thought it would be cool to rebuild it from scratch on an RPI5. And here we are.</p>

<h2>RPI-VOICE-ASSISTANT</h2>

<p>The strength of Rpi-voice-assistant is that it can use both <strong>OpenAI</strong> and <strong>Mistral</strong> (and in the future, other APIs too), with automatic fallback and easy switching between them.</p>

<ul>
    <li><strong>Outside your home:</strong> you can use OpenAI.</li>
    <li><strong>Don’t want to pay OpenAI?</strong> You can run a Mistral server API locally on your PC.</li>
    <li><strong>with <code>BaseHandler</code>, it’s easy to extend it to other APIs and use it as a generic LLM class. Beyond just a chatbot, it’s also simple to make multi-purpose agents.</li>
  
</ul>

<p>The name might not be original.</p>

<h2>How to talk with BMO right now: </h2>
<h3>0. (Not optional) Obviusly you have to install the models, i used </h3>
<ul>

  <li><a href="https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_GB/semaine/medium" target="_blank">Piper Voices (en_GB semaine medium)</a></li>
  <li><a href="https://huggingface.co/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF/blob/main/Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf" target="_blank">Nous Hermes 2 Mistral 7B DPO</a></li>
  <li>vosk-model-small-en-us-0.15</li>

  
</ul>
<h3>1. (Optional) Mistral – on your PC</h3>
<ol>
    <li>Copy only the <code>.mistralserver</code> directory</li>
    <li><code>python -m venv venv</code></li>
    <li><code>source venv/bin/activate</code></li>
    <li><code>pip install -r requirements.txt</code></li>
    <li>Modify <code>config.py</code> with the absolute path of your Mistral model and its settings</li>
    <li><code>python3 api_server2.py</code></li>
</ol>

<h3>2. On the Raspberry Pi 5</h3>
<ol>
    <li><code>python -m venv venv</code></li>
    <li><code>source venv/bin/activate</code></li>
    <li><code>pip install -r requirements.txt</code></li>
    <li>Modify <code>config.json</code> with the paths of your Vosk model, Piper model, and (if set) the URL of your local Mistral API server</li>
</ol>

</body>
</html>

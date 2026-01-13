<body>
  
<h1>BMO (A Local AI companion on Raspberry Pi 5)</h1>

<p>I literally want to build BMO.</p>
<p>What is BMO? <br>
<strong>--> He’s BMO.</strong></p>

<img src="https://media4.giphy.com/media/v1.Y2lkPTZjMDliOTUyNTUwczA1YWZvem94em9ncjdrMGZyZXFuZWlyYzh6a2Q4aWh6OGpkMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/10bxTLrpJNS0PC/giphy.gif" alt="bmo" width="500">

<p>I found an old project for an RPi 3 and thought it would be cool to rebuild it from scratch on an RPi 5. And here we are. It can recognize simple objects and talk to you.</p>
<p>I am also working on facial and voice recognition, as well as letting him play games with you.</p>

<h2>RPI Voice assistant with OpenAI/Mistral</h2>

<p>The strength of Rpi-voice-assistant is that it can use both <strong>OpenAI</strong> and <strong>Mistral</strong> (and other APIs in the future), with automatic fallback and easy switching between them.</p>

<ul>
    <li><strong>Outside your home:</strong> You can use OpenAI.</li>
    <li><strong>Don’t want to pay for OpenAI?</strong> You can run a local Mistral API server on your PC.</li>
    <li><strong>With <code>BaseHandler</code>:</strong> It’s easy to extend to other APIs and use it as a generic LLM class. Beyond just a chatbot, it’s simple to build multi-purpose agents.</li>
</ul>

<p>I know, the name might not be original, but, I mean, I'm building BMO so what other name should I use?.</p>

<h2>Hardware</h2>
<ol>
  <li>Raspberry Pi 5</li>
  <li>Active Cooler (Please make sure to buy the official 'ACTIVE' one)</li>
  <li>Speakers</li>
  <li>IMX219 Camera with Pi 5 Flat cable</li>
  <li>Lavalier Microphone (I used one I already had with a USB adapter)</li>
  <li>7'' Display compatible with Raspberry Pi</li>
</ol>

<h2>How to talk with BMO right now:</h2>
<h3>0. (Required) Install the models</h3>
<ul>
  <li><a href="https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_GB/semaine/medium" target="_blank">Piper Voices (en_GB semaine medium)</a></li>
  <li><a href="https://huggingface.co/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF/blob/main/Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf" target="_blank">Nous Hermes 2 Mistral 7B DPO</a></li>
  <li>vosk-model-small-en-us-0.15 (Already installed in <code>BMO/stt</code>! For other languages, see below)</li>
</ul>

<h3>1. (Optional) Mistral – on your PC</h3>
<ol>
    <li>Copy only the <code>.mistralserver</code> directory</li>
    <li><code>python -m venv venv</code></li>
    <li><code>source venv/bin/activate</code></li>
    <li><code>pip install -r requirements.txt</code></li>
    <li>Modify <code>config.py</code> with the absolute path of your Mistral model and settings</li>
    <li><code>python3 api_server2.py</code></li>
</ol>

<h3>2. On the Raspberry Pi 5</h3>
<ol>
    <li><code>python -m venv venv</code></li>
    <li><code>source venv/bin/activate</code></li>
    <li><code>pip install -r requirements.txt</code></li>
    <br>
    <strong>Configuration:</strong>
    <li>Modify <code>config.json</code> with the paths for your Vosk model, Piper model, and (if set) the URL of your local Mistral API server</li>
    <li>Change the extension of <code>BMO/handlers/.env.example</code> to <code>BMO/handlers/.env</code> and insert your OPENAI API-KEY</li>
  <br>
    <li><code>python3 main.py</code></li>
</ol>

<h3>For other languages:</h3>
<p>I'm working on adding all prompts to <code>config.json</code> to make them easier to translate. In the meantime, you can install the Vosk model for your language and add it to <code>config.json</code>.</p>

</body>

# Integrador iOS (Atalhos + Pushcut)

Servidor MCP que permite ao Claude executar **Atalhos** (Shortcuts) no seu iPhone.

## Como funciona

O iOS é sandboxed: nenhum app externo consegue controlar outros apps diretamente,
sem jailbreak. A forma oficial de automatizar ações no iPhone a partir de um
servidor é através do app **Atalhos** da Apple, disparado remotamente pelo app
[Pushcut](https://www.pushcut.io/), que expõe um webhook secreto capaz de
executar um Atalho específico.

Fluxo: `Claude → este servidor MCP → webhook do Pushcut → iPhone → Atalho`

O Atalho é quem de fato interage com os apps (abrir um app, tocar música,
criar lembrete, enviar mensagem, etc.) — o integrador só aciona a execução.

## Pré-requisitos

1. iPhone com o app **Atalhos** (nativo) e o app **Pushcut** instalados.
2. No Pushcut: Settings → Account → copiar o **webhook secret**.
3. No Pushcut: habilitar o Atalho desejado na lista de *Automation Server
   enabled Shortcuts* (Settings → Automation Server), para que ele possa ser
   executado remotamente. Isso requer o Pushcut Pro.
4. Criar/ter o Atalho pronto no app Atalhos, com o nome exato que será usado
   nas chamadas.

## Instalação

```bash
cd ios-integrator
pip install -r requirements.txt
```

Defina o segredo do webhook como variável de ambiente:

```bash
export PUSHCUT_SECRET="seu-secret-do-pushcut"
```

## Registrar no Claude Code

```bash
claude mcp add ios-shortcuts --env PUSHCUT_SECRET="seu-secret-do-pushcut" -- python3 "$(pwd)/server.py"
```

Ou, no Claude Desktop, adicione ao `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ios-shortcuts": {
      "command": "python3",
      "args": ["/caminho/completo/para/ios-integrator/server.py"],
      "env": { "PUSHCUT_SECRET": "seu-secret-do-pushcut" }
    }
  }
}
```

## Uso

Depois de configurado, basta pedir ao Claude, por exemplo:

> "Rode o atalho 'Tocar Playlist Foco' no meu iPhone"

O Claude vai chamar a ferramenta `run_shortcut(shortcut="Tocar Playlist Foco")`.

## Segurança

O `PUSHCUT_SECRET` dá acesso de execução aos seus Atalhos habilitados no
Automation Server. Trate-o como uma senha: não faça commit dele no
repositório e não o compartilhe.

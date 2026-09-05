# Avisa Mãe

App Android que resolve o problema de mensagens/ligações do WhatsApp que passam
despercebidas: quando a pessoa configurada (ex.: você) manda mensagem ou liga
pelo WhatsApp — ou faz uma ligação comum — o celular mostra uma **tela cheia
por cima de qualquer outro app**, inclusive sobre a tela bloqueada, com a
mensagem e botões grandes para responder, ligar de volta ou fechar.

Não existe uma "máscara" que cubra o Android inteiro o tempo todo (isso não é
permitido pelo sistema, por segurança), mas o efeito prático que você quer —
"ela não vai conseguir ignorar, vai aparecer na cara dela" — é conseguido com
o mesmo mecanismo que o Android usa para ligações recebidas e alarmes:
notificação de prioridade máxima + tela cheia (`fullScreenIntent`).

## Como funciona

1. **NotificationService** fica ouvindo as notificações do sistema. Quando o
   WhatsApp (`com.whatsapp` ou `com.whatsapp.w4b`) posta uma notificação de
   mensagem ou ligação de um nome configurado, o alerta é disparado.
2. **CallReceiver** faz o mesmo para ligações comuns (fora do WhatsApp), caso
   o número bata com o telefone configurado.
3. **AlertLauncher** dispara a tela (`AlertActivity`) de duas formas ao mesmo
   tempo (para funcionar até em aparelhos mais restritivos como Xiaomi/Samsung
   com economia de bateria agressiva):
   - Notificação com `setFullScreenIntent` + `CATEGORY_CALL` + prioridade
     máxima (mecanismo oficial do Android, o mesmo de chamadas/alarmes).
   - Tentativa direta de abrir a tela (funciona na maioria dos aparelhos,
     porque serviços de notificação têm permissão do sistema pra isso).
4. **AlertActivity** é a tela cheia: nome de quem mandou, mensagem, toca som e
   vibra até a mãe tocar em um botão ("Abrir WhatsApp", "Ligar de volta",
   "Atender ligação" ou "Fechar"). O botão "voltar" do Android é ignorado de
   propósito, para garantir que o aviso seja visto.

## Como compilar e instalar

Este é um projeto Gradle/Android Studio padrão.

1. Abra a pasta `AvisaMae/` no **Android Studio** (Iguana ou mais recente).
2. Deixe o Gradle sincronizar (baixa as dependências automaticamente).
3. Conecte o celular da sua mãe via USB com "Depuração USB" ativada, ou gere
   um APK: `Build > Build Bundle(s) / APK(s) > Build APK(s)`.
4. Instale o APK no aparelho dela (pode ser direto pelo Android Studio, ou
   transferindo o `.apk` e instalando manualmente — nesse caso ela precisará
   permitir "instalar de fontes desconhecidas" uma única vez).

## Configuração no celular dela (uma vez só)

Abra o app **Avisa Mãe** e:

1. Preencha o **nome exatamente como aparece no WhatsApp dela** para você
   (o nome que está salvo na agenda dela para o seu contato — é esse nome que
   aparece no topo da notificação do WhatsApp). Pode colocar mais de um nome
   separado por vírgula.
2. Preencha o(s) **telefone(s)** que podem ligar (separados por vírgula se
   houver mais de um). O primeiro número da lista é o usado pelos botões
   "Ligar de volta" e "Abrir WhatsApp".
3. Toque em **"Salvar configuração"**.
4. Toque em **"1. Permitir acesso às notificações"** → na tela que abrir,
   ative o "Avisa Mãe" (é o que permite o app ler que chegou mensagem do
   WhatsApp).
5. Toque em **"2. Permitir telefone e chamadas"** e aceite as permissões.
6. Toque em **"3. Ignorar otimização de bateria"** → isso é essencial;
   sem isso, o Android pode "matar" o app em segundo plano e o alerta
   simplesmente não dispara depois de um tempo.
7. Toque em **"4. Permitir notificações em tela cheia"** (só aparece em
   Android 14+) e ative.
8. Toque em **"Testar alerta agora"** para conferir que a tela cheia aparece
   corretamente, inclusive com a tela bloqueada.

Em aparelhos Xiaomi (MIUI), Samsung, Huawei, Oppo/Realme, etc., também vale a
pena procurar em Ajustes por "Início automático" / "Autostart" / "Apps
protegidos" e liberar o Avisa Mãe — esses fabricantes têm uma camada extra de
gerenciamento de bateria além da configuração padrão do Android.

## Limitações importantes (para alinhar expectativa)

- O app só reage a **mensagens/ligações do WhatsApp** e a **ligações comuns**
  do número configurado — ele não intercepta SMS, Telegram, etc. (dá pra
  estender se você precisar).
- O nome configurado precisa **bater com o nome salvo no WhatsApp dela** para
  o seu contato. Se ela salvou você com um apelido diferente do que você
  digitou na configuração, o alerta não dispara — ajuste o texto conforme o
  nome real que aparece nas notificações do WhatsApp dela.
- Em alguns aparelhos com gerenciamento de bateria muito agressivo, mesmo
  com tudo configurado, o Android pode atrasar a notificação por alguns
  segundos — é do sistema, não do app.
- Não é preciso (e o app não usa) a permissão "Exibir sobre outros apps"
  (`SYSTEM_ALERT_WINDOW`), que é cada vez mais restrita pelo Google e pelos
  fabricantes. O mecanismo de `fullScreenIntent` é o caminho suportado e mais
  estável para esse tipo de alerta.

# Meu Primeiro PR

Este é um repositório de prática criado para aprender o fluxo de Pull Requests no GitHub: branch, commit, push e revisão.

## Como este repo funciona

1. Uma branch é criada a partir da `main`.
2. Uma pequena melhoria é feita nessa branch.
3. Um Pull Request é aberto para revisão antes do merge.

## Monta Look — app de guarda-roupa

App web simples (HTML/CSS/JS puro, sem backend) para cadastrar suas peças de roupa e gerar sugestões de look.

### Como usar

1. Abra `index.html` no navegador (ou rode um servidor local: `python3 -m http.server` e acesse `http://localhost:8000`).
2. Na aba **Meu Guarda-roupa**, cadastre suas peças (nome, categoria, cor e foto opcional).
3. Na aba **Montar Look**, clique em "Gerar look" para receber uma combinação aleatória com uma avaliação simples de harmonia de cores (neutra, monocromática, contraste proposital etc.).
4. Salve os looks que gostar na aba **Looks Salvos**.

Os dados ficam salvos no `localStorage` do navegador — nada é enviado para um servidor.

## Licença

Este projeto é apenas para fins de aprendizado e não possui licença formal.

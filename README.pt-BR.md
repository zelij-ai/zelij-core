# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · **Português (Brasil)** · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**Monte sua startup 100 % nativa em IA.** Um escritório onde quatro agentes trabalham para você: eles propõem, você decide. Sua máquina, sua chave Claude, seus dados; nada "liga para casa".

![O aquário do Zelij Core: o fundador e quatro agentes conversam, propõem decisões e executam o que foi aprovado](docs/img/aquarium.gif)

*O aquário em um dia simulado (aqui em francês). Na sua instalação, cada cartão é uma ação real dos seus agentes, ao vivo e com replay de vinte e quatro horas. O ouro é você: nada que comprometa acontece antes da sua decisão. Os rostos são de personagens fictícios.*

## O que o núcleo faz

- **O escritório**: uma página. As decisões pendentes, um pedido ao chefe de gabinete, as últimas execuções com seu custo, o diário, os agentes, os módulos instalados.
- **O pacote de decisão**: objetivo, proposta, por que agora, opções, recomendação, riscos, reversibilidade, plano, reversão, impacto. Um pacote incompleto não abre. Aprovar, recusar ou pedir mudanças com uma instrução obrigatória repassada ao agente.
- **As regras da casa**: nada que comprometa (dinheiro, exposição pública, exclusão, irreversível) é feito sem decisão; um fato tem data e fonte ou é marcado como "não verificado"; o diário nunca é apagado.
- **O gateway**: a chave Claude do fundador, o custo de cada chamada calculado a partir do uso e das tarifas públicas datadas, um teto mensal que bloqueia.
- **O executor**: um laço de chamadas limitado (orçamento de turnos por agente), ferramentas sóbrias, uma recusa do modelo tratada como resultado.
- **Os módulos**: a única forma de estender o núcleo. Interface estável, manifesto `pack.json` assinado pelo editor com Ed25519, hash de cada arquivo coberto pela assinatura, verificação antes da instalação. Alvos de implantação e agentes adicionais passam por aqui.
- **Finanças**: vendas confirmadas (importação do Stripe somente leitura ou lançamento com comprovante), despesas declaradas que se repetem todo mês, custo dos agentes medido, diário do mês, exportação CSV para o contador. Nada é declarado nem faturado.
- **Contatos**: uma ficha por pessoa, base legal obrigatória, prazo de retenção, trocas, direitos exercidos; um contato que se opõe não recebe mais nada, um contato vencido é esquecido e só o diário de direitos permanece.
- **Publicação**: uma página escrita pelo agente de marketing vira rascunho, depois decisão; aprovada, é proposta ao site como pull request no GitHub ou rascunho no WordPress. O último gesto, mesclar ou publicar, é seu.
- **No bolso**: cada decisão chega ao seu telefone, por e-mail com dois links assinados de uso único, ou pelo Telegram com três botões. Você aprova na fila do metrô; o aquário se move assim que você responde. A mesma porta, o mesmo diário de quando está na mesa.
- **Aquário**: veja seus agentes trabalhando; cada bolha é uma ação real das últimas 24 horas, os anéis pontilhados são vagas abertas. Uma página pública compartilhável, com o selo "by zelij.ai".
- **Catálogo**: o que a edição livre não contém, nomeado com honestidade; um módulo comprado do editor é instalado aqui, assinado e verificado. Nenhum pagamento passa pelo escritório.
- **Software factory**: o Construtor lê e propõe em um único repositório, por pull requests que passam pelo portão de segurança (300 linhas, só texto, nenhum segredo, nenhum arquivo de infraestrutura, dependências sem vulnerabilidade conhecida via OSV); implantação em um servidor Linux por SSH ou na OVH (domínio e DNS pela API) com troca atômica, teste de fumaça e reversão; sonda do domínio; backup diário do escritório. Ele nunca mescla, nunca paga, nunca toca no escritório.
- **Os agentes**: uma pasta por agente, um `agent.md` com cabeçalho simples e instruções em francês. Quatro agentes: Camille Aubert (chefe de gabinete), Élise Tanguy (crescimento, marketing e produtos), Nour Bellamy (finanças e clientes), Sacha Ferrand (construtor, software factory). O fundador fala com cada um a partir do escritório; um pacote aprovado que indica um agente e uma tarefa é executado na hora, dentro dos limites do plano.

## Experimente em um minuto, sem chave

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

Abra `http://localhost:8000` e entre na demonstração: uma empresa fictícia, quatro agentes simulados, decisões para aprovar, o aquário reproduzindo o dia deles. Nenhuma chave, nenhuma conta, nenhum custo; nada é enviado a um modelo e tudo desaparece ao parar. Quando estiver convencido, passe para a instalação real abaixo. O escritório em si está em francês.

## Iniciar

```bash
cp .env.example .env     # chave Claude, teto, SECRET_KEY, senha do banco
docker compose up -d --build
```

O escritório responde em `http://localhost:8000`. Sem SMTP, o link de login é gravado nos logs do contêiner (`docker compose logs core-app`).

Guias completos (em inglês): **[Instalação](docs/INSTALLATION.en.md)** (máquina vazia → escritório em https, SMTP, software factory, backups, solução de problemas), **[Manual de uso](docs/MODE-D-EMPLOI.en.md)** (cada página, os agentes, as decisões, o custo). As fotos do fundador e dos agentes vão em [`portraits/`](portraits/README.md) (descrição em francês).

A partir da imagem publicada, sem build local (`CORE_IMAGE_TAG=v…` no `.env` fixa a versão):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Localmente sem Docker:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Chave pública do editor

Os módulos do catálogo são assinados pela zelij.ai. A chave pública a colocar em `ZELIJ_CLE_PUBLIQUE` (já preenchida em `.env.example`):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Segurança

O que o núcleo garante, e que é testado (`tests/test_securite.py`):

- **Módulos**: um módulo só é instalado e executado se assinado pelo editor (Ed25519), e a assinatura cobre o hash SHA-256 de cada arquivo de código: um arquivo modificado, adicionado ou removido após a assinatura tira o módulo de jogo.
- **Login**: links de uso único de 20 minutos, com hash no banco; freios por endereço, por IP e global nos pedidos de link, para que o escritório nunca sirva de relé de e-mail; sem SMTP configurado em produção, nenhum link é criado nem registrado.
- **Formulários**: cookie de sessão HMAC `HttpOnly` `SameSite=Strict`, verificação de origem e token anti-CSRF por sessão em cada POST.
- **Páginas**: política de segurança de conteúdo estrita (`default-src 'self'`, nenhum script inline, nenhum frame), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS quando a origem é https.
- **Agentes**: o que um agente lê (página web, arquivo do repositório) chega a ele enquadrado como conteúdo externo, nunca como instrução; um agente executa apenas as ferramentas da sua ficha e, assim que leu um dado privado, só pode chamar o site da empresa; só lê endereços https públicos (endereços privados, de loopback, link-local e nomes internos recusados a cada salto de redirecionamento, resposta limitada); o portão de segurança bloqueia segredos, arquivos de infraestrutura, scripts de terceiros, frames e chamadas de rede.
- **Contêiner**: usuário sem privilégios, sistema de arquivos somente leitura, nenhuma capability, sem elevação; a chave do servidor SSH pode ser fixada (`SSH_CLE_HOTE`).
- **Exportação contábil**: células que parecem uma fórmula de planilha são neutralizadas.

Relate uma falha a `securite@zelij.ai`, sem publicá-la antes da correção. Antes de cada versão, `pip-audit -r requirements.txt` e `bandit -r core scripts -ll` devem voltar vazios.

## Contribuir e acompanhar as versões

`CONTRIBUTING.md` (em francês) explica como uma contribuição entra em uma versão, incluindo a regra: um alvo de implantação contribuído vale o pacote correspondente grátis para sempre. `SECURITY.md` explica como relatar uma falha. `CHANGELOG.md` diz o que cada versão muda e o que resta ao fundador fazer.

## Testes e controle de publicação

```bash
python -m pytest -q
python scripts/controle_publication.py
```

O controle de publicação recusa chaves, endereços IP, códigos internos, endereços de e-mail pessoais, senhas em texto claro e os termos de uma lista privada (`ZELIJ_CORE_INTERDITS`) que nunca faz parte do repositório.

## Licença

GNU AGPL v3. Copyright (C) 2026 zelij.ai. Você pode usar, modificar e redistribuir o núcleo, desde que publique suas modificações sob a mesma licença. A edição completa que faz a zelij.ai funcionar continua sendo a do editor.

by zelij.ai — https://zelij.ai/

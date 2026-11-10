# 📉 Monitor de Preços

Ferramenta de linha de comando em **Python** que acompanha o preço de produtos em lojas online, guarda o histórico, gera gráficos e **avisa quando o preço cai abaixo do valor que você quer pagar**.

![Gráfico de exemplo](docs/produto_exemplo.png)

## O que ele faz

- Descobre o preço automaticamente na página do produto
- Guarda o histórico de preços em CSV
- Mostra a variação desde a última consulta (▲ / ▼)
- Gera um gráfico da evolução do preço com a linha do preço alvo
- Avisa no terminal e, opcionalmente, **por e-mail** quando o preço chega no alvo
- Pode rodar sozinho todos os dias com o Agendador de Tarefas do Windows

## Como o preço é encontrado

A maioria das lojas coloca os dados do produto na página de um jeito padronizado para o Google ler. O monitor tenta, nesta ordem:

1. **Seletor CSS** informado por você (para lojas que precisam de ajuste manual)
2. **JSON-LD** (`schema.org/Product`), usado pela maioria dos e-commerces
3. **Meta tags** de preço (`product:price:amount`, `og:price:amount`, `itemprop="price"`)

Ele também entende os formatos de preço brasileiro e internacional: `R$ 1.299,90`, `1,299.90`, `49,90`…

## Tecnologias

- Python 3.10+
- [Requests](https://requests.readthedocs.io/) para baixar as páginas
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) para ler o HTML
- [Matplotlib](https://matplotlib.org/) para os gráficos
- [pytest](https://pytest.org/) para os testes automatizados

## Instalação

```bash
git clone https://github.com/menguevtr/monitor-de-precos.git
cd monitor-de-precos
python -m venv .venv
.venv\Scripts\activate        # no Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Como usar

```bash
# Começar a monitorar um produto (o alvo é o preço que você quer pagar)
python monitor.py adicionar "Fone JBL" "https://www.loja.com.br/fone-jbl" --alvo 199.90

# Ver os produtos monitorados
python monitor.py listar

# Consultar os preços agora (é este comando que você agenda)
python monitor.py verificar

# Gerar o gráfico do produto de id 1 (salvo em dados/graficos/)
python monitor.py grafico 1

# Parar de monitorar
python monitor.py remover 1
```

Exemplo de saída:

```
ID  PRODUTO                                  ATUAL         MENOR          ALVO
------------------------------------------------------------------------------
1   Fone JBL                             R$ 219,90     R$ 209,90     R$ 199,90
2   Teclado mecânico                     R$ 189,90     R$ 189,90     R$ 199,90 🔔
```

### Quando a loja não é reconhecida

Se aparecer “Não encontrei o preço nesta página”, informe onde o preço está com um seletor CSS:

1. Abra a página do produto no navegador
2. Clique com o botão direito no preço → **Inspecionar**
3. Veja a classe do elemento (por exemplo `<span class="price-final">`)
4. Use `--seletor`:

```bash
python monitor.py adicionar "Livro" "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html" --alvo 60 --seletor ".product_main .price_color"
```

> Algumas lojas grandes bloqueiam acessos automáticos ou carregam o preço com JavaScript. Nesses casos o monitor pode não conseguir ler o preço.

## Alerta por e-mail (opcional)

O e-mail usa variáveis de ambiente, assim nenhuma senha fica salva no código. Com Gmail, crie uma **senha de app** em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) e configure no PowerShell:

```powershell
setx ALERTA_EMAIL_REMETENTE "seuemail@gmail.com"
setx ALERTA_EMAIL_SENHA "sua-senha-de-app"
setx ALERTA_EMAIL_DESTINO "seuemail@gmail.com"
```

Feche e abra o terminal de novo para as variáveis valerem.

## Rodando todos os dias automaticamente (Windows)

Crie uma tarefa no Agendador de Tarefas que roda o `verificar` todo dia às 9h (ajuste os caminhos para a pasta do projeto):

```powershell
schtasks /create /sc daily /st 09:00 /tn "Monitor de Precos" /tr "C:\caminho\monitor-de-precos\.venv\Scripts\python.exe C:\caminho\monitor-de-precos\monitor.py verificar"
```

## Testes

```bash
python -m pytest
```

Os testes cobrem a conversão de preços, a extração por JSON-LD, meta tags e seletor CSS, a regra dos alertas, o histórico e a geração do gráfico. Nenhum teste acessa a internet.

## Estrutura

```
monitor-de-precos/
├── monitor.py            # comandos de linha (adicionar, listar, verificar…)
├── precos/
│   ├── extrator.py       # baixa a página e encontra o preço
│   ├── armazenamento.py  # produtos (JSON) e histórico (CSV)
│   ├── alertas.py        # alerta no terminal e por e-mail
│   └── grafico.py        # gráfico do histórico
├── tests/                # testes automatizados
└── dados/                # criada ao usar (não vai para o GitHub)
```

## Uso responsável

Use para acompanhar poucos produtos, com consultas espaçadas (uma ou duas vezes por dia), e respeite os termos de uso de cada site. O monitor espera alguns segundos entre uma loja e outra para não sobrecarregar os servidores.

## Próximos passos

- [ ] Alerta pelo Telegram
- [ ] Suporte a páginas que carregam o preço com JavaScript (Playwright)
- [ ] Interface web com Streamlit
- [ ] Rodar na nuvem com GitHub Actions

---

Feito por [Vitor Dorneles](https://github.com/menguevtr) · [LinkedIn](https://www.linkedin.com/in/vitor-mengue-dorneles/)

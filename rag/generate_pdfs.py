# Gerador de Documentos PDF de RH
# Gera 5 PDFs fictícios para o HR Onboarding Agent

from fpdf import FPDF
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

class HRPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, "Recursos Humanos - Documento Oficial", align="C", new_x="LMARGIN", new_y="NEXT")
        self.line(10, 18, 200, 18)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Confidencial - Uso Interno | Página {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Arial", "B", 14)
        self.set_text_color(33, 37, 41)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 123, 255)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def body_text(self, text):
        self.set_font("Arial", "", 11)
        self.set_text_color(73, 80, 87)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Arial", "", 11)
        self.set_text_color(73, 80, 87)
        self.cell(5)
        self.cell(5, 6, chr(8226))
        self.multi_cell(0, 6, text)
        self.ln(1)

DOCUMENTS = {
    "politica_ferias.pdf": {
        "title": "Política de Férias",
        "sections": [
            ("1. Período Aquisitivo e Gozo", 
             "Todo colaborador tem direito a 30 dias corridos de férias após completar 12 meses de trabalho (período aquisitivo), conforme artigo 130 da CLT. As férias devem ser gozadas nos 12 meses subsequentes ao período aquisitivo (período concessivo)."),
            ("2. Escala de Gozo",
             "As férias podem ser fracionadas em até 3 períodos, sendo que um deles não pode ser inferior a 14 dias corridos e os demais não podem ser inferiores a 5 dias corridos cada. O colaborador deve solicitar as férias com no mínimo 30 dias de antecedência. A empresa se reserva o direito de aprovar ou reprogramar o período solicitado com base nas necessidades operacionais."),
            ("3. Abono Pecuniário",
             "O colaborador pode converter até 1/3 do período de férias em abono pecuniário (vender até 10 dias). O pedido deve ser feito até 15 dias antes do término do período aquisitivo. O valor do abono corresponde ao salário normal acrescido do adicional de 1/3 constitucional."),
            ("4. Férias Coletivas",
             "A empresa pode conceder férias coletivas a um ou mais setores por até 20 dias corridos, mediante comunicação ao Ministério do Trabalho e aos sindicatos com no mínimo 15 dias de antecedência. Colaboradores com menos de 12 meses de casa recebem férias proporcionais."),
            ("5. Regras Importantes",
             "Nao e permitido acumular mais de 2 períodos de ferias sem gozo. As ferias nao gozadas dentro do periodo concessivo devem ser pagas em dobro. Durante as ferias, o colaborador recebe o salario normal acrescido de 1/3 constitucional."),
        ]
    },
    "beneficios.pdf": {
        "title": "Guia de Benefícios",
        "sections": [
            ("1. Plano de Saúde",
             "A empresa oferece plano de saúde Unimed Nacional (enfermaria) para todos os colaboradores registrados, com coparticipação de 20% em consultas e exames. O plano cobre consultas, exames laboratoriais, internações, cirurgias e atendimento de emergência em todo o território nacional. Dependentes (cônjuge, filhos até 24 anos estudantes) podem ser incluídos com custo adicional de R$ 180,00 por dependente. A carência é de 90 dias para consultas e 180 dias para internações."),
            ("2. Vale Alimentação / Refeição",
             "Vale alimentação no valor de R$ 800,00 mensais creditado no cartão Flash até o dia 5 de cada mês. Vale refeição no valor de R$ 35,00 por dia útil para colaboradores presenciais, também no cartão Flash. Os valores sao recarregados automaticamente e podem ser utilizados em restaurantes, supermercados e delivery credenciados."),
            ("3. Vale Transporte",
             "A empresa fornece vale transporte conforme a legislação, com desconto de até 6% do salário base do colaborador. O valor excedente é custeado integralmente pela empresa. Colaboradores em regime de home office não recebem vale transporte, salvo quando convocados para reuniões ou eventos presenciais (nesses casos o transporte é reembolsado)."),
            ("4. Seguro de Vida",
             "Seguro de vida em grupo no valor de R$ 50.000,00 para todos os colaboradores, com cobertura por morte natural ou acidental, invalidez permanente total ou parcial por acidente, e assistência funerária. O seguro é custeado integralmente pela empresa, sem qualquer desconto para o colaborador."),
            ("5. Gympass / Wellhub",
             "Acesso ao Wellhub (antigo Gympass) nos planos Básico e Silver, com desconto de 50% para upgrades. O benefício inclui academias, estúdios de yoga, pilates e aplicativos de bem-estar em todo o Brasil. A adesão é voluntária e pode ser feita a qualquer momento pelo portal do Wellhub."),
            ("6. Auxílio Home Office",
             "Colaboradores em regime de home office recebem auxílio mensal de R$ 150,00 para despesas de internet e energia elétrica. O valor é pago juntamente com o salário e não precisa ser comprovado via notas fiscais."),
        ]
    },
    "codigo_conduta.pdf": {
        "title": "Código de Conduta",
        "sections": [
            ("1. Princípios Gerais",
             "Este Código de Conduta estabelece as diretrizes de comportamento esperadas de todos os colaboradores, independentemente do cargo ou tempo de empresa. Espera-se que todos ajam com integridade, respeito, responsabilidade e transparência em todas as situações profissionais. O descumprimento das regras pode resultar em advertências, suspensões ou demissão por justa causa."),
            ("2. Horário de Trabalho",
             "A jornada regular é de 8 horas diárias (44 horas semanais), de segunda a sexta-feira, com horário flexível entre 7h e 19h. O colaborador deve cumprir 8 horas líquidas de trabalho com intervalo mínimo de 1 hora de almoço. O registro de ponto é obrigatório para todos os colaboradores, inclusive em home office, e deve ser feito no sistema PontoTel até as 9h e ao final do expediente."),
            ("3. Dress Code",
             "O ambiente de trabalho adota estilo business casual. Não é permitido uso de shorts, regatas, chinelos ou roupas com estampas ofensivas. Em home office, recomenda-se trajes adequados para videoconferências (pelo menos da cintura para cima). Sextas-feiras são dias de traje livre (casual), respeitando o bom senso."),
            ("4. Uso de Recursos Corporativos",
             "Os equipamentos, sistemas e rede corporativos devem ser utilizados exclusivamente para fins profissionais. Não é permitido acessar sites de conteúdo impróprio, jogar, baixar software não autorizado ou utilizar a internet corporativa para atividades pessoais durante o horário de trabalho. E-mails corporativos não devem ser utilizados para cadastros pessoais."),
            ("5. Confidencialidade",
             "Todas as informações internas da empresa, incluindo dados financeiros, estratégias, projetos, informações de clientes e colaboradores, são confidenciais e não podem ser divulgadas sem autorização expressa da liderança. Ao deixar a empresa, o colaborador deve devolver todos os equipamentos e arquivos corporativos."),
            ("6. Assédio e Discriminação",
             "A empresa tolera zero condutas de assédio moral, sexual ou discriminação de qualquer natureza (raça, gênero, religião, orientação sexual, idade ou deficiência). Casos devem ser reportados imediatamente ao RH ou ao canal de denúncias anônimo disponível no portal interno. Todas as denúncias são investigadas sigilosamente."),
        ]
    },
    "politica_home_office.pdf": {
        "title": "Política de Home Office",
        "sections": [
            ("1. Regime de Trabalho",
             "A empresa adota o modelo híbrido: 3 dias presenciais e 2 dias remotos por semana. Os dias presenciais são definidos pelo gestor imediato e devem ser comunicados com no mínimo 1 semana de antecedência. Colaboradores de outras cidades (fora da sede) podem solicitar regime integralmente remoto, sujeito a aprovação da diretoria."),
            ("2. Dias Permitidos",
             "Colaboradores podem trabalhar remotamente até 2 dias por semana, preferencialmente terça, quarta ou quinta (segunda e sexta são dias de maior presença esperada). Excepcionalmente, mediante aprovação do gestor, é possível realizar até 5 dias remotos consecutivos em caso de necessidade (obra em casa, problema de saúde familiar, etc.)."),
            ("3. Equipamentos",
             "A empresa fornece notebook corporativo, monitor adicional (mediante solicitação), headset e mouse. O colaborador é responsável por manter os equipamentos em bom estado e devolvê-los ao desligamento. Não é permitido o uso de equipamentos pessoais para atividades corporativas que envolvam dados sensíveis. Em caso de problemas técnicos, contatar o suporte de TI pelo e-mail ti@empresa.com ou pelo ramal 1234."),
            ("4. Disponibilidade e Comunicação",
             "Durante o home office, o colaborador deve estar disponível e responder às mensagens do Slack em até 15 minutos no horário comercial (9h às 18h). A participação em reuniões agendadas é obrigatória, com câmera ligada sempre que possível. O status no Slack deve ser mantido atualizado (disponível, em reunião, pausa, etc.)."),
            ("5. Saúde e Ergonomia",
             "O colaborador deve manter um ambiente de trabalho adequado em casa, com boa iluminação, cadeira confortável e postura correta. A empresa oferece, mediante solicitação, avaliação ergonômica remota e subsídio de até R$ 300,00 para aquisição de cadeira ou mesa adequadas (uma vez a cada 2 anos). Pausas de 5 a 10 minutos a cada 2 horas são recomendadas."),
        ]
    },
    "onboarding_geral.pdf": {
        "title": "Guia de Onboarding - Primeiros Dias",
        "sections": [
            ("1. Seu Primeiro Dia",
             "Seu primeiro dia começa às 9h na recepção do escritório (andar térreo). Traga documento com foto para o cadastro. Seu gestor ou um buddy designado vai te receber e fazer um tour pelo escritório. No primeiro dia, você vai receber seu notebook, crachá de acesso e acesso aos sistemas. Vista-se em business casual no primeiro dia. Se for remoto, seu gestor enviará um link do Zoom para a boas-vindas virtual."),
            ("2. Quem Contatar",
             "RH: rh@empresa.com ou ramal 2000 (respondem dúvidas sobre benefícios, folha de pagamento e documentos). TI: ti@empresa.com ou ramal 1234 (problemas técnicos, acesso a sistemas). Gestor direto: seu primeiro ponto de contato para dúvidas sobre trabalho, metas e prioridades. Buddy: um colega designado para te ajudar na integração com o time e a cultura da empresa."),
            ("3. Sistemas que Você Vai Usar",
             "Slack - comunicação interna (canais: #geral, #onboarding, #seutime). Google Workspace - e-mail, calendário e documentos. PontoTel - registro de ponto diário. PipeDrive - CRM (se aplicável ao seu cargo). Notion - documentação interna e wikis. Jira - gestão de tarefas (se aplicável ao seu cargo). Wellhub - benefício de academias. Flash - cartão de alimentação e refeição."),
            ("4. Treinamentos Obrigatórios",
             "Nos primeiros 15 dias, você deve completar: (1) Treinamento de Segurança da Informação (1h, plataforma EAD), (2) Código de Conduta (leitura e termo de ciência), (3) Apresentação da Cultura e Valores da Empresa (2h presencial ou Zoom), (4) Treinamento dos sistemas que utilizará no dia a dia. Todos os treinamentos são agendados pelo RH e você receberá os links por e-mail."),
            ("5. Checklist da Primeira Semana",
             "[ ] Receber equipamentos e acessos. [ ] Configurar assinatura de e-mail. [ ] Entrar nos canais do Slack. [ ] Agendar café com cada membro do time (15 min cada). [ ] Ler o Código de Conduta e assinar termo de ciência. [ ] Conferir os benefícios no portal do RH. [ ] Baixar os aplicativos: Slack, Flash, Wellhub. [ ] Confirmar dados bancários para folha de pagamento."),
            ("6. Período de Experiência",
             "O período de experiência é de 90 dias, podendo ser prorrogado por mais 90 dias (total 180 dias). Durante esse período, tanto o colaborador quanto a empresa podem rescindir o contrato sem justa causa com aviso prévio de 30 dias ou indenização proporcional. Ao final dos primeiros 45 dias, o gestor realizará uma avaliação de desempenho com feedback formal."),
        ]
    }
}


def generate_pdfs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for filename, doc in DOCUMENTS.items():
        pdf = HRPDF()
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # Title page
        pdf.set_font("Arial", "B", 24)
        pdf.set_text_color(0, 123, 255)
        pdf.ln(40)
        pdf.cell(0, 15, doc["title"], align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(108, 117, 125)
        pdf.cell(0, 10, "Documento interno de Recursos Humanos", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, "Versao 1.0 - Vigente a partir de Janeiro de 2025", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        pdf.set_draw_color(0, 123, 255)
        pdf.line(60, pdf.get_y(), 150, pdf.get_y())
        pdf.ln(30)
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(108, 117, 125)
        pdf.cell(0, 8, "Este documento contem informacoes confidenciais da empresa.", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, "Nao deve ser compartilhado com pessoas externas a organizacao.", align="C", new_x="LMARGIN", new_y="NEXT")

        # Content pages
        pdf.add_page()
        for title, text in doc["sections"]:
            pdf.section_title(title)
            pdf.body_text(text)

        output_path = os.path.join(OUTPUT_DIR, filename)
        pdf.output(output_path)
        print(f"[OK] {filename} gerado - {len(doc['sections'])} secoes")

    print(f"\nTodos os {len(DOCUMENTS)} PDFs gerados em: {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_pdfs()

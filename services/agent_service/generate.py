import os
import time
import numpy as np
import streamlit as st
import pdfplumber
import spacy
from collections import Counter
from dotenv import load_dotenv
from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Initialize French Spacy model
try:
    nlp = spacy.load("fr_core_news_md")
except OSError:
    st.error(
        "Please install French Spacy model: `python -m spacy download fr_core_news_md`"
    )
    st.stop()


def analyze_style(text):
    """Analyze French text style characteristics across all 10 categories"""
    doc = nlp(text)
    sentences = list(doc.sents)

    # 1. Vocabulary & Diction
    avg_sentence_length = (
        sum(len(sent) for sent in sentences) / len(sentences) if sentences else 0
    )
    common_verbs = ", ".join(
        {token.lemma_.lower() for token in doc if token.pos_ == "VERB"}
    )
    common_adjectives = ", ".join(
        {token.lemma_.lower() for token in doc if token.pos_ == "ADJ"}
    )
    complex_words_ratio = (
        sum(1 for token in doc if len(token.text) > 6) / len(doc) if len(doc) > 0 else 0
    )

    # Recurring bigrams (excluding stopwords/punctuation)
    bigrams = []
    prev_token = None
    for token in doc:
        if (
            prev_token
            and not token.is_punct
            and not prev_token.is_punct
            and not token.is_stop
            and not prev_token.is_stop
        ):
            bigrams.append((prev_token.lemma_.lower(), token.lemma_.lower()))
        prev_token = token
    top_bigrams = [f"{a} {b}" for (a, b), _ in Counter(bigrams).most_common(5)]

    # Slang detection (example terms)
    slang_terms = {
        "bagnole",
        "bouffer",
        "truc",
        "mec",
        "nana",
        "fric",
        "boulot",
        "taffe",
        "ouf",
    }
    slang_count = sum(1 for token in doc if token.text.lower() in slang_terms)

    # 2. Sentence Structure
    syntax_complexity = (
        sum(1 for token in doc if token.pos_ == "SCONJ") / len(sentences)
        if sentences
        else 0
    )
    sentence_length_std = (
        np.std([len(sent) for sent in sentences]) if len(sentences) > 1 else 0
    )

    # 3. Tone & Mood (simplified formality)
    formality_score = (
        sum(1 for token in doc if "Mood=Ind" in token.morph) / len(doc)
        if len(doc) > 0
        else 0
    )

    # 4. Figurative Language
    similes = sum(
        1
        for sent in sentences
        for i, token in enumerate(sent)
        if token.text.lower() == "comme"
        and i < len(sent) - 1
        and sent[i + 1].pos_ in ["NOUN", "ADJ"]
    )

    # Imagery categories (example terms)
    visual_adj = {"beau", "brillant", "coloré", "sombre", "clair"}
    auditory_adj = {"bruyant", "silencieux", "sonore", "mélodieux"}
    tactile_adj = {"doux", "rugueux", "lisse", "dur"}
    imagery = {
        "visual": sum(1 for token in doc if token.lemma_.lower() in visual_adj),
        "auditory": sum(1 for token in doc if token.lemma_.lower() in auditory_adj),
        "tactile": sum(1 for token in doc if token.lemma_.lower() in tactile_adj),
    }

    # 5. Narrative Voice
    narrative_voice = {
        "first_person": sum(
            1 for token in doc if token.lemma_.lower() in {"je", "nous"}
        ),
        "third_person": sum(
            1
            for token in doc
            if token.lemma_.lower() in {"il", "elle", "ils", "elles", "on"}
        ),
    }

    # 7. Themes & Motifs
    nouns = [
        token.lemma_.lower()
        for token in doc
        if token.pos_ == "NOUN" and not token.is_stop
    ]
    top_nouns = [noun for noun, _ in Counter(nouns).most_common(5)]

    # Extract top entities (corrected)
    top_entities = [
        ent_text
        for ent_text, _ in Counter([ent.text for ent in doc.ents]).most_common(5)
    ]

    # 8. Dialogue Style
    quotes = sum(1 for token in doc if token.text in ['"', "«", "»"])

    # 9. Stylistic Quirks
    fragments = sum(
        1 for sent in sentences if not any(token.pos_ == "VERB" for token in sent)
    )
    repetitions = sum(
        len(
            set(sent1.lemma_ for sent1 in sent)
            & set(sent2.lemma_ for sent2 in next_sent)
        )
        for sent, next_sent in zip(sentences, sentences[1:])
    )

    # 10. Descriptive Style
    avg_adj_adv = (
        (sum(1 for token in doc if token.pos_ in ["ADJ", "ADV"]) / len(sentences))
        if sentences
        else 0
    )

    return {
        "avg_sentence_length": avg_sentence_length,
        "common_verbs": common_verbs,
        "common_adjectives": common_adjectives,
        "formality_score": formality_score,
        "complex_words_ratio": complex_words_ratio,
        "top_bigrams": top_bigrams,
        "slang_count": slang_count,
        "syntax_complexity": syntax_complexity,
        "sentence_length_std": sentence_length_std,
        "similes": similes,
        "imagery": imagery,
        "narrative_voice": narrative_voice,
        "top_nouns": top_nouns,
        "top_entities": top_entities,
        "quotes": quotes,
        "fragments": fragments,
        "repetitions": repetitions,
        "avg_adj_adv": avg_adj_adv,
    }


def generate_blog(topic: str, style_features: dict):
    """Generate French blog post using enhanced style features"""
    examples = [
        {
            "input": "l'impact de l'IA sur l'emploi",
            "output": """## L'essor des machines intelligentes : menace ou opportunité ?

**Introduction**  
Depuis une décennie, l'intelligence artificielle bouleverse nos paysages professionnels. Des usines automatisées aux logiciels de gestion prédictive, cette révolution technologique soulève autant d'espoirs que d'inquiétudes.

**Section 1 : Les métiers en mutation**  
Le secteur manufacturier a perdu 15% de ses emplois depuis 2015, remplacés par des robots capables de travailler 24h/24. Paradoxalement, de nouveaux métiers émergent : analyste de données, éthicien IA, formateur en reconversion professionnelle...

**Section 2 : L'adaptation nécessaire**  
Les compétences transversales deviennent cruciales. Comme l'affirme Marc Durand, expert en futur du travail : *"La flexibilité cognitive sera le sésame des prochaines décennies."* Les systèmes éducatifs doivent intégrer davantage de philosophie technologique et de gestion du changement.

**Conclusion**  
Plutôt qu'une apocalypse annoncée, l'IA pourrait constituer un formidable accélérateur d'évolution professionnelle, à condition d'accompagner activement les transitions.""",
        },
        {
            "input": "les enjeux climatiques urbains",
            "output": """## Villes vertes : utopie ou réalité prochaine ?

**Le défi urbain**  
Face à l'urgence écologique, nos métropoles se réinventent. Amsterdam prévoit d'atteindre la neutralité carbone d'ici 2030 grâce à un plan ambitieux combinant énergie solaire, mobilité douce et agriculture verticale.

**Infrastructures du futur**  
Les "forêts verticales" milanaises, couvrant des gratte-ciel entiers de végétation, réduisent jusqu'à 30% la pollution atmosphérique locale. Singapour a investi 2 milliards dans des "corridors climatiques" connectant tous ses parcs.

**Obstacles persistants**  
Malgré ces innovations, le manque de coordination internationale et les intérêts économiques à court terme freinent les progrès. Comme le souligne le rapport de l'ONU-Environnement 2023, seules 12% des villes disposent d'un plan climatique contraignant.

**Perspectives**  
L'avenir urbain réside dans une approche systémique : intégrer biodiversité, circularité énergétique et participation citoyenne. Les premières "éco-cités" chinoises montrent des résultats prometteurs, avec une réduction de 40% des déchets ménagers.""",
        },
    ]

    example_prompt = ChatPromptTemplate.from_messages(
        [("human", "Rédige un article sur : {input}"), ("ai", "{output}")]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=examples,
    )

    system_template = """Tu es un rédacteur expert francophone. Respecte ces consignes :
    - Longueur : Minimum 800 mots, 5 sections structurées
    - Style : {tone} avec des transitions fluides
    - Structure : Titre percutant, introduction choc, 3-5 sous-sections détaillées, conclusion impactante
    - Éléments requis : 
      * 2-3 citations explicites (ex: "Selon l'étude X...")
      * Des données chiffrées crédibles
      * Au moins {similes} comparaisons/concrétisations
      * Vocabulaire technique modéré ({complex_words_ratio:.0%} de termes complexes)

    Produis un article complet et détaillé EXCLUSIVEMENT en français.
    """

    system_message = SystemMessagePromptTemplate.from_template(system_template)

    full_prompt = ChatPromptTemplate.from_messages(
        [
            system_message,
            few_shot_prompt,
            HumanMessagePromptTemplate.from_template(
                "Rédige un article détaillé sur : {topic}"
            ),
        ]
    )

    llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=0.7,
        max_tokens=3000,
        openai_api_key=os.getenv("OPEN_AI_KEY"),
    )
    return (full_prompt | llm).invoke(
        {
            "topic": topic,
            **style_features,
            "tone": "formel" if style_features["formality_score"] > 0.7 else "informel",
        }
    )


# Streamlit UI
st.set_page_config(page_title="French Blog Generator", page_icon="✍️")

# Step 1: PDF Processinganalyze_style
st.title("✍️ Milestone 1")

if "processed" not in st.session_state:
    st.session_state.processed = False

with st.expander(
    "STEP 1: Analyze Writing Style", expanded=not st.session_state.processed
):
    uploaded_files = st.file_uploader(
        "Upload your French style PDF(s)", type="pdf", accept_multiple_files=True
    )

    process_btn = st.button("Analyze Combined Style")

    if process_btn and uploaded_files and not st.session_state.processed:
        with st.spinner("Analyzing writing style from multiple PDFs..."):
            source_text = ""

            # Process all uploaded PDFs
            for uploaded_file in uploaded_files:
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            source_text += text + "\n"

            # Add visual processing animation
            progress_bar = st.progress(0)
            analysis_status = st.empty()

            # Simulate processing steps
            steps = [
                ("Concatenating documents...", 25),
                ("Tokenizing text...", 50),
                ("Analyzing syntax patterns...", 75),
                ("Finalizing style profile...", 100),
            ]

            for text, progress in steps:
                analysis_status.info(f"⏳ {text}")
                progress_bar.progress(progress)
                time.sleep(0.8)

            # Perform actual analysis
            st.session_state.style_features = analyze_style(source_text)
            st.session_state.processed = True

            # Cleanup progress elements
            progress_bar.empty()
            analysis_status.empty()

            # Show summary
            st.success(
                f"✅ Analyzed {len(uploaded_files)} PDF(s) with {len(source_text.split())} total words!"
            )
            st.caption(
                f"Processed files: {', '.join([f.name for f in uploaded_files])}"
            )

# Step 2: Blog Generation
if st.session_state.processed:
    with st.expander("STEP 2: Generate Blog Post", expanded=True):
        blog_topic = st.text_input(
            "Enter your blog topic:",
            placeholder="e.g.: L'avenir de l'éducation numérique",
        )

        if st.button("Generate French Article"):
            with st.spinner("Crafting your unique article..."):
                start_time = time.time()
                result = generate_blog(blog_topic, st.session_state.style_features)
                generation_time = time.time() - start_time

                st.subheader("Generated French Blog")
                st.caption(f"⏱ Generation time: {generation_time:.2f} seconds")
                st.markdown("---")
                st.markdown(result.content)
                st.success("French blog generated successfully!")

# Style Metrics Sidebar
if st.session_state.processed:
    with st.sidebar:
        st.header("📊 Style Analysis Report")
        # Existing metrics
        st.metric(
            "Avg Sentence Length",
            f"{st.session_state.style_features['avg_sentence_length']:.1f} words",
        )
        st.write("**Common Verbs:**", st.session_state.style_features["common_verbs"])
        st.write(
            "**Frequent Adjectives:**",
            st.session_state.style_features["common_adjectives"],
        )
        st.write(
            "**Formality Level:**",
            (
                "Formal"
                if st.session_state.style_features["formality_score"] > 0.7
                else "Casual"
            ),
        )

        # New metrics
        st.subheader("Vocabulary & Diction")
        st.metric(
            "Complex Words Ratio",
            f"{st.session_state.style_features['complex_words_ratio']:.1%}",
        )
        st.write(
            "**Top Bigrams:**",
            ", ".join(st.session_state.style_features["top_bigrams"]),
        )
        st.write(
            "**Slang Terms Count:**", st.session_state.style_features["slang_count"]
        )

        st.subheader("Sentence Structure")
        st.metric(
            "Syntax Complexity",
            f"{st.session_state.style_features['syntax_complexity']:.2f}/phrase",
        )
        st.metric(
            "Sentence Length Variation",
            f"σ {st.session_state.style_features['sentence_length_std']:.2f}",
        )

        st.subheader("Figurative Language")
        st.write("**Similes:**", st.session_state.style_features["similes"])
        st.write(
            f"**Imagery:** 👁️ {st.session_state.style_features['imagery']['visual']} | 👂 {st.session_state.style_features['imagery']['auditory']} | ✋ {st.session_state.style_features['imagery']['tactile']}"
        )

        st.subheader("Narrative Voice")
        narrative = st.session_state.style_features["narrative_voice"]
        st.write(
            f"**Perspective:** 1st Person ({narrative['first_person']}), 3rd Person ({narrative['third_person']})"
        )

        st.subheader("Themes & Motifs")
        st.write(
            "**Top Nouns:**", ", ".join(st.session_state.style_features["top_nouns"])
        )
        st.write(
            "**Frequent Entities:**",
            ", ".join(st.session_state.style_features["top_entities"]),
        )

        st.subheader("Stylistic Quirks")
        st.write(
            "**Sentence Fragments:**", st.session_state.style_features["fragments"]
        )
        st.write(
            "**Lexical Repetitions:**", st.session_state.style_features["repetitions"]
        )

        st.subheader("Descriptive Style")
        st.metric(
            "Adjectives/Adverbs per Sentence",
            f"{st.session_state.style_features['avg_adj_adv']:.1f}",
        )

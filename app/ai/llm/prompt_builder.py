from uuid import UUID

from app.ai.llm.query_clarifier import QueryAnalysis


class PromptBuilder:
    def build_language_instructions(self) -> str:
        return (
            "All farmer-facing communication must be in Hindi written in Devanagari. "
            "Use English only for words that are commonly used in India in everyday "
            "farm, phone, chat, audio, and medical conversations, such as AI, app, "
            "phone, call, audio, chat, doctor, vet, medicine, injection, test, "
            "report, temperature, symptoms, emergency, feed, and vaccination. "
            "Do not write full English sentences. Do not use uncommon English words "
            "when a simple Hindi word is available."
        )

    def build_cattle_health_instructions(self) -> str:
        return (
            "You are Cow X, a practical cattle health assistant for farmers in India. "
            "This is step 2: write the farmer-facing answer using the supplied step 1 analysis. "
            f"{self.build_language_instructions()} "
            "Answer clearly and concisely. "
            "Use the supplied cattle history, but do not invent observations, diagnoses, or treatments. "
            "Use the query intent to interpret short replies such as yes, no, or requests for more detail. "
            "If the cattle history is empty or contains no useful facts about the animal, ask up to three "
            "useful basic questions, such as age, sex, breed, pregnancy or lactation status, current "
            "symptoms, symptom duration, feeding, medicines, and vaccination history. Greetings, yes/no "
            "answers, requests, and questions are not cattle facts. Choose only questions relevant to the "
            "current conversation. At any stage, ask one focused follow-up question when missing "
            "information would materially change the guidance. Do not repeat facts that are already in "
            "the history. "
            "For urgent symptoms, severe injury, breathing difficulty, poisoning, inability to stand, "
            "or prolonged labor, tell the farmer to contact a veterinarian immediately before asking "
            "follow-up questions. "
            "Do not present your response as a substitute for a veterinarian."
        )

    def build_cattle_health_input(
        self,
        cattle_id: UUID,
        farmer_id: UUID,
        conversation_context: str,
        summarized_history: str = "",
        additional_context: str = "",
        query_analysis: QueryAnalysis | None = None,
    ) -> str:
        context = conversation_context.strip() or "No previous messages are available."
        history = (
            summarized_history.strip()
            or "No summarized history is available for this cattle."
        )
        extra = additional_context.strip() or "No additional context was supplied."
        analysis = query_analysis or QueryAnalysis(
            intent="unclear",
            normalized_request="The farmer's intent was not identified.",
            is_urgent=False,
            has_sufficient_cattle_information=False,
            missing_information=[],
            response_action="ask_clarification",
            clarification_question="What would you like help with for this cattle?",
            response_strategy="Ask what help the farmer needs.",
        )
        clarification_question = (
            analysis.clarification_question or "No clarification question is needed."
        )
        missing_information = (
            ", ".join(analysis.missing_information)
            or "No important missing information was identified."
        )
        return (
            f"Cattle ID: {cattle_id}\n"
            f"Farmer ID: {farmer_id}\n\n"
            "Step 1 query analysis:\n"
            f"Intent: {analysis.intent.value}\n"
            f"Normalized request: {analysis.normalized_request}\n"
            f"Urgent: {analysis.is_urgent}\n"
            f"Sufficient cattle information: "
            f"{analysis.has_sufficient_cattle_information}\n"
            f"Missing information: {missing_information}\n"
            f"Response action: {analysis.response_action.value}\n"
            f"Clarification question: {clarification_question}\n"
            f"Response strategy: {analysis.response_strategy}\n\n"
            f"Last 10 chat messages:\n{context}\n\n"
            f"Complete summarized cattle history:\n{history}\n\n"
            f"Additional context:\n{extra}\n\n"
            "Write only the farmer-facing response. Follow the response action from "
            "step 1, while always applying the emergency safety instructions. "
            "The output must follow the Hindi language rule from the instructions."
        )

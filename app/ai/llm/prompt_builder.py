from uuid import UUID

from app.ai.llm.query_clarifier import QueryAnalysis


class PromptBuilder:
    def build_language_instructions(self) -> str:
        return (
            "All farmer-facing communication must be in Hindi written in Devanagari. "
            "Use a warm, colloquial, rural Hindi dialect that a farmer speaks. Avoid overly formal "
            "or Sanskritized Hindi words where common spoken farm terms exist (e.g., use simple terms "
            "like doodh, gabhan/garbhvati, bimar, etc.). Mix in commonly understood English/Hinglish "
            "terms naturally, such as doctor, vet, medicine, injection, feed, vaccine, limit, check, and report. "
            "Do not write full English sentences."
        )

    def build_cattle_health_instructions(self) -> str:
        return (
            "You are Cow X, a practical cattle health assistant for farmers in India. "
            "This is step 2: write the farmer-facing answer using the supplied step 1 analysis. "
            f"{self.build_language_instructions()} "
            "Answer clearly and concisely in short sentences. If recommending actions, remedies, or "
            "feed schedules, list them in simple, numbered steps. Do not output long blocks of text "
            "that are hard to listen to or understand over voice channels. "
            "Use the supplied cattle profile and history, but do not invent observations, "
            "diagnoses, or treatments. "
            "The cattle name and tag number are already known from the profile; never ask "
            "the farmer to repeat them. "
            "Use the query intent to interpret short replies such as yes, no, or requests for more detail. "
            "If the cattle history is empty or contains no useful facts about the animal, ask exactly "
            "one focused, high-priority basic question (such as age, breed, pregnancy/lactation status, "
            "or symptoms) rather than grouping multiple questions together. Greetings, yes/no "
            "answers, requests, and questions are not cattle facts. Choose only one question relevant to the "
            "current conversation. At any stage, ask at most one focused follow-up question when missing "
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
        cattle_profile: str,
        conversation_context: str,
        summarized_history: str = "",
        additional_context: str = "",
        query_analysis: QueryAnalysis | None = None,
    ) -> str:
        profile = cattle_profile.strip() or (
            f"Cattle ID: {cattle_id}\nFarmer ID: {farmer_id}"
        )
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
            f"Cattle profile from database:\n{profile}\n\n"
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
            "Use the database profile for the animal identity. "
            "The output must follow the Hindi language rule from the instructions."
        )

    def build_memory_extraction_instructions(self) -> str:
        return (
            "Extract durable cattle facts from the latest farmer message. "
            "Store only information that could help future cattle care conversations. "
            "Do not store greetings, questions, requests, acknowledgements, or facts already "
            "present in the supplied profile/history unless the latest message updates them. "
            "Classify each fact as medical, feeding, breeding, milk, medicine, or general. "
            "Use medical for symptoms, illness, injury, veterinary observations, pregnancy/labor "
            "risk, and health status. Use general for identity and stable background details. "
            "Always call save_cattle_memories exactly once."
        )

    def build_memory_extraction_input(
        self,
        cattle_profile: str,
        conversation_context: str,
        summarized_history: str,
        latest_user_message: str,
        additional_context: str = "",
    ) -> str:
        context = conversation_context.strip() or "No previous messages are available."
        history = (
            summarized_history.strip()
            or "No summarized history is available for this cattle."
        )
        extra = additional_context.strip() or "No additional context was supplied."
        return (
            f"Cattle profile from database:\n{cattle_profile}\n\n"
            f"Recent conversation:\n{context}\n\n"
            f"Stored cattle history:\n{history}\n\n"
            f"Additional context:\n{extra}\n\n"
            f"Latest farmer message:\n{latest_user_message}"
        )

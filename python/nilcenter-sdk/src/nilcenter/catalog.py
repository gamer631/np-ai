"""Built-in, offline-first laboratory catalog."""

from __future__ import annotations

from nilcenter.models import LabDescriptor

_LABS: tuple[LabDescriptor, ...] = (
    LabDescriptor("cybersecurity", "Cybersecurity & Defensive Testing", "Authorized security research, defensive validation and digital forensics.", ("security", "forensics", "defense")),
    LabDescriptor("reverse-engineering", "Reverse Engineering", "Static analysis, debugging, disassembly and isolated sample analysis.", ("binary analysis", "debugging", "malware analysis")),
    LabDescriptor("ai-ml", "AI & Machine Learning", "Model development, inference, evaluation and reproducible experiments.", ("machine learning", "models", "agents")),
    LabDescriptor("software-engineering", "Software Engineering", "Programming, compilers, debugging, testing and release engineering.", ("development", "testing", "devtools")),
    LabDescriptor("network-research", "Network & Protocol Research", "Protocol inspection, packet analysis and network diagnostics.", ("protocols", "networking", "diagnostics")),
    LabDescriptor("hardware-electronics", "Hardware & Electronics", "Circuit research, firmware, microcontrollers and hardware debugging.", ("electronics", "firmware", "embedded")),
    LabDescriptor("robotics", "Robotics & Automation", "Robotics simulation, control systems and automation research.", ("robotics", "simulation", "control")),
    LabDescriptor("cloud-infrastructure", "Cloud & Infrastructure", "Containers, infrastructure-as-code and observability.", ("cloud", "containers", "operations")),
    LabDescriptor("data-science", "Data Science & Analytics", "Data preparation, statistics, visualization and pipelines.", ("data", "statistics", "analytics")),
    LabDescriptor("scientific-computing", "Scientific Computing", "Numerical methods and scientific simulations.", ("mathematics", "physics", "simulation")),
    LabDescriptor("quantum-computing", "Quantum Computing", "Quantum circuit design, simulation and algorithms.", ("quantum", "circuits", "algorithms")),
    LabDescriptor("innovation-prototyping", "Innovation & Prototyping", "Rapid prototypes, experiments and proof-of-concepts.", ("prototyping", "experiments", "innovation")),
)


class LabCatalog:
    """Read-only catalog that works without network access."""

    def list(self) -> tuple[LabDescriptor, ...]:
        """Return all known laboratories in stable order."""
        return _LABS

    def get(self, lab_id: str) -> LabDescriptor:
        """Find a laboratory by its stable identifier."""
        normalized = lab_id.strip().lower()
        for lab in _LABS:
            if lab.id == normalized:
                return lab
        raise KeyError(f"Unknown NILcenter laboratory: {lab_id}")

    def search(self, query: str) -> tuple[LabDescriptor, ...]:
        """Search laboratory identifiers, names, summaries and focus areas."""
        needle = query.strip().casefold()
        if not needle:
            return self.list()
        return tuple(
            lab
            for lab in _LABS
            if needle in " ".join((lab.id, lab.name, lab.summary, *lab.focus_areas)).casefold()
        )

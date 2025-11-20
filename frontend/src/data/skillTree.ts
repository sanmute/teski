export type SkillDefinition = {
  id: string;
  name: string;
  description: string;
  category: "Foundations" | "Core" | "Advanced";
  prerequisites: string[];
};

export const SKILL_DEFINITIONS: SkillDefinition[] = [
  {
    id: "skill_fundamentals",
    name: "Study Fundamentals",
    description: "Keep a steady cadence and nail spaced repetition basics.",
    category: "Foundations",
    prerequisites: [],
  },
  {
    id: "skill_limits",
    name: "Limits",
    description: "Understand how functions behave near points.",
    category: "Foundations",
    prerequisites: ["skill_fundamentals"],
  },
  {
    id: "skill_derivatives",
    name: "Derivatives",
    description: "Differentiate functions and interpret rates of change.",
    category: "Core",
    prerequisites: ["skill_limits"],
  },
  {
    id: "skill_applications",
    name: "Derivative Applications",
    description: "Optimization, motion, and practical rate problems.",
    category: "Core",
    prerequisites: ["skill_derivatives"],
  },
  {
    id: "skill_integrals",
    name: "Integrals",
    description: "Area under curves, accumulation, and antiderivatives.",
    category: "Core",
    prerequisites: ["skill_derivatives"],
  },
  {
    id: "skill_techniques",
    name: "Integration Techniques",
    description: "Substitution, integration by parts, trig tricks.",
    category: "Advanced",
    prerequisites: ["skill_integrals"],
  },
  {
    id: "skill_series",
    name: "Series & Convergence",
    description: "Infinite sums, Taylor polynomials, and convergence tests.",
    category: "Advanced",
    prerequisites: ["skill_integrals"],
  },
  {
    id: "skill_diff_eq",
    name: "Differential Equations",
    description: "First-order and separable equations, modeling change.",
    category: "Advanced",
    prerequisites: ["skill_integrals", "skill_applications"],
  },
  {
    id: "skill_multivar",
    name: "Multivariable Calc",
    description: "Partial derivatives, gradients, multivariate optimization.",
    category: "Advanced",
    prerequisites: ["skill_derivatives"],
  },
];

export const SKILL_ROOTS = SKILL_DEFINITIONS.filter((def) => def.prerequisites.length === 0).map(
  (def) => def.id,
);

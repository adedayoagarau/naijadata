// Nigerian State Governors Data
// Last updated: 2025

export interface Governor {
  state: string;
  slug: string;
  name: string;
  party: "APC" | "PDP" | "LP" | "APGA" | "ACCORD" | "NNPP";
  since: number; // Year took office
  imageUrl?: string;
}

export const governors: Governor[] = [
  { state: "Abia", slug: "abia", name: "Alex Otti", party: "LP", since: 2023 },
  { state: "Adamawa", slug: "adamawa", name: "Ahmadu Fintiri", party: "PDP", since: 2019 },
  { state: "Akwa Ibom", slug: "akwa-ibom", name: "Umo Eno", party: "PDP", since: 2023 },
  { state: "Anambra", slug: "anambra", name: "Charles Soludo", party: "APGA", since: 2022 },
  { state: "Bauchi", slug: "bauchi", name: "Bala Mohammed", party: "PDP", since: 2019 },
  { state: "Bayelsa", slug: "bayelsa", name: "Douye Diri", party: "PDP", since: 2020 },
  { state: "Benue", slug: "benue", name: "Hyacinth Alia", party: "APC", since: 2023 },
  { state: "Borno", slug: "borno", name: "Babagana Zulum", party: "APC", since: 2019 },
  { state: "Cross River", slug: "cross-river", name: "Bassey Otu", party: "APC", since: 2023 },
  { state: "Delta", slug: "delta", name: "Sheriff Oborevwori", party: "PDP", since: 2023 },
  { state: "Ebonyi", slug: "ebonyi", name: "Francis Nwifuru", party: "APC", since: 2023 },
  { state: "Edo", slug: "edo", name: "Monday Okpebholo", party: "APC", since: 2024 },
  { state: "Ekiti", slug: "ekiti", name: "Biodun Oyebanji", party: "APC", since: 2022 },
  { state: "Enugu", slug: "enugu", name: "Peter Mbah", party: "PDP", since: 2023 },
  { state: "FCT", slug: "fct", name: "Nyesom Wike", party: "PDP", since: 2023 },
  { state: "Gombe", slug: "gombe", name: "Inuwa Yahaya", party: "APC", since: 2019 },
  { state: "Imo", slug: "imo", name: "Hope Uzodinma", party: "APC", since: 2020 },
  { state: "Jigawa", slug: "jigawa", name: "Umar Namadi", party: "APC", since: 2023 },
  { state: "Kaduna", slug: "kaduna", name: "Uba Sani", party: "APC", since: 2023 },
  { state: "Kano", slug: "kano", name: "Abba Yusuf", party: "NNPP", since: 2023 },
  { state: "Katsina", slug: "katsina", name: "Dikko Radda", party: "APC", since: 2023 },
  { state: "Kebbi", slug: "kebbi", name: "Nasir Idris", party: "APC", since: 2023 },
  { state: "Kogi", slug: "kogi", name: "Usman Ododo", party: "APC", since: 2024 },
  { state: "Kwara", slug: "kwara", name: "AbdulRahman AbdulRazaq", party: "APC", since: 2019 },
  { state: "Lagos", slug: "lagos", name: "Babajide Sanwo-Olu", party: "APC", since: 2019 },
  { state: "Nasarawa", slug: "nasarawa", name: "Abdullahi Sule", party: "APC", since: 2019 },
  { state: "Niger", slug: "niger", name: "Mohammed Bago", party: "APC", since: 2023 },
  { state: "Ogun", slug: "ogun", name: "Dapo Abiodun", party: "APC", since: 2019 },
  { state: "Ondo", slug: "ondo", name: "Lucky Aiyedatiwa", party: "APC", since: 2024 },
  { state: "Osun", slug: "osun", name: "Ademola Adeleke", party: "PDP", since: 2022 },
  { state: "Oyo", slug: "oyo", name: "Seyi Makinde", party: "PDP", since: 2019 },
  { state: "Plateau", slug: "plateau", name: "Caleb Mutfwang", party: "PDP", since: 2023 },
  { state: "Rivers", slug: "rivers", name: "Siminalayi Fubara", party: "PDP", since: 2023 },
  { state: "Sokoto", slug: "sokoto", name: "Ahmad Aliyu", party: "APC", since: 2023 },
  { state: "Taraba", slug: "taraba", name: "Agbu Kefas", party: "PDP", since: 2023 },
  { state: "Yobe", slug: "yobe", name: "Mai Mala Buni", party: "APC", since: 2019 },
  { state: "Zamfara", slug: "zamfara", name: "Dauda Lawal", party: "PDP", since: 2023 },
];

export const getGovernorByState = (slug: string): Governor | undefined => {
  return governors.find((g) => g.slug === slug.toLowerCase());
};

export const getGovernorsByParty = (party: Governor["party"]): Governor[] => {
  return governors.filter((g) => g.party === party);
};

export const partyColors: Record<Governor["party"], string> = {
  APC: "#008751", // Green
  PDP: "#E63946", // Red
  LP: "#487A3A", // Dark Green
  APGA: "#9E7D45", // Brown
  ACCORD: "#164678", // Blue
  NNPP: "#D6453A", // Orange-Red
};

export const partyFullNames: Record<Governor["party"], string> = {
  APC: "All Progressives Congress",
  PDP: "Peoples Democratic Party",
  LP: "Labour Party",
  APGA: "All Progressives Grand Alliance",
  ACCORD: "Accord Party",
  NNPP: "New Nigeria Peoples Party",
};

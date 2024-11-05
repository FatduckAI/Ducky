import { analyzeSentiment } from "@/src/lib/together.sentiment";

const result = await analyzeSentiment("Please kindly check my pm sir");
console.log(result);

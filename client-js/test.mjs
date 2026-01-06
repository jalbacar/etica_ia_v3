// client-js/test.mjs
import Lego from "./index.mjs";

(async () => {
  try {
    const result = await Lego.checkAll("test sesgo");
    console.log(result);
  } catch (error) {
    console.error("Error:", error);
  }
})();

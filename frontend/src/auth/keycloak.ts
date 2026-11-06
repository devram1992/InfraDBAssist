import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: "http://localhost:8080",
  realm: "infradb",
  clientId: "infradb-assist",
});

let initialization: Promise<boolean> | undefined;

export function initializeKeycloak(): Promise<boolean> {
  if (!initialization) {
    initialization = keycloak.init({
      onLoad: "login-required",
      pkceMethod: "S256",
      checkLoginIframe: false,
    });
  }

  return initialization;
}

export default keycloak;

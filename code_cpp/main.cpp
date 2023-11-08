#include "util.hpp"

// JSON doc : https://github.com/nlohmann/json

signed main() {
	ios::sync_with_stdio(false);
	cout.tie(0); cin.tie(0);
	cout << fixed << setprecision(10);

    json in_data = read_input("test.json");
    json sol_data = in_data;
    cout << in_data << endl;
    output_sol_force_overwrite("test.json", sol_data);


    // Example
	json j = json::parse(R"({"happy": false, "pi": 3.141})");
    j["happy"] = true;
    j["bonjour"] = "[\"hello\"]"_json;
    j["hello"] = R"(["bonjour", 3.5])"_json;
    j["hello"].push_back(json::array()); // Build []
    j["hello"].push_back(json::object()); // Build {}
    cout << j << endl;
}
#include "json.hpp"
#include <iostream>
#include <vector>
#include <deque>
#include <map>
#include <set>
#include <unordered_set>
#include <string>
#include <fstream>


using namespace std;
using namespace nlohmann;

using lli = long long int;
using ulli = unsigned long long int;
const int INF = 1e9;
const lli LLINF = 4*1e18;

// const string OUT_SUFFIX = "-out-1";
const string OUT_SUFFIX = "";

json read_input(string name) {
    std::ifstream ifs("../inputs/" + name);
    std::string content( (std::istreambuf_iterator<char>(ifs) ),
                        (std::istreambuf_iterator<char>()    ) );
    return json::parse(content);
}

string _out_with_suffix(string name) {
    int n = name.size();
    return name.substr(0, n-5) + OUT_SUFFIX + name.substr(n-5, 5);
}

json read_sol(string name) {
    std::ifstream ifs("../sols/" + _out_with_suffix(name));
    std::string content( (std::istreambuf_iterator<char>(ifs) ),
                        (std::istreambuf_iterator<char>()    ) );
    return json::parse(content);
}

void output_sol_force_overwrite(string name, json data) {
    std::ofstream ofs("../sols/" + _out_with_suffix(name));
    ofs << data.dump();
}



/* COUT << ANYTHING */

template<class T> ostream& operator<<(ostream& os, const vector<T>& v);
template<class T> ostream& operator<<(ostream& os, const deque<T>& v);
template<class T, size_t s> ostream& operator<<(ostream& os, const array<T, s>& v);
template<class T> ostream& operator<<(ostream& os, const set<T>& v);
template<class A, class B> ostream& operator<<(ostream& os, const map<A, B>& v);
template<class T> ostream& operator<<(ostream& os, const unordered_set<T>& v);
template<class A, class B> ostream& operator<<(ostream& os, const unordered_map<A, B>& v);
template<class A, class B> ostream& operator<<(ostream& os, const pair<A, B>& el);

template<class T> ostream& operator<<(ostream& os, const vector<T>& v) { os << "[ "; for (auto& el : v) { os << el << ", "; } os << "]"; return os; }
template<class T> ostream& operator<<(ostream& os, const deque<T>& v) { os << "[ "; for (auto& el : v) { os << el << ", "; } os << "]"; return os; }
template<class T, size_t s> ostream& operator<<(ostream& os, const array<T, s>& v) { os << "[ "; for (auto& el : v) { os << el << ", "; } os << "]"; return os; }
template<class T> ostream& operator<<(ostream& os, const set<T>& v) { os << "( "; for (auto& el : v) { os << el << ", "; } os << ")"; return os; }
template<class A, class B> ostream& operator<<(ostream& os, const map<A, B>& v) { os << "{ "; for (auto& el : v) { os << el.first << ": " << el.second << ", "; } os << "}"; return os; }
template<class T> ostream& operator<<(ostream& os, const unordered_set<T>& v) { os << "( "; for (auto& el : v) { os << el << ", "; } os << ")"; return os; }
template<class A, class B> ostream& operator<<(ostream& os, const unordered_map<A, B>& v) { os << "{ "; for (auto& el : v) { os << el.first << ": " << el.second << ", "; } os << "}"; return os; }
template<class A, class B> ostream& operator<<(ostream& os, const pair<A, B>& el) { os << "(" << el.first << ", " << el.second << ")"; return os; }
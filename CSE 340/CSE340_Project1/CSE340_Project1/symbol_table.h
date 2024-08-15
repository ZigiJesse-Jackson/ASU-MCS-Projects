#include <string>
#include <unordered_map>
using namespace std;
class SymbolTable {
    // bool indicates if var was declared public or private
    // false for public, true for private
    unordered_map<string, bool> var_names;
    string scope_name;
    public:
        bool find_var(const string& name);
        bool check_var_visibility(const string& name);
        void add_var(const string& name, bool priv);
        string get_scope();
        SymbolTable(const string& name);
};
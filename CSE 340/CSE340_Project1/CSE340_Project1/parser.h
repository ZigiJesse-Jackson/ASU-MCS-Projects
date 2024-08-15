#include "unordered_map"
#include "lexer.h"
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


class Global_Table{
    string global;
    unordered_map<string, SymbolTable*> tables;
    public:
        bool find_var(const string& name, const string& scope);
        bool find_var(const string& name);        
        bool add_var(const string& name, const string& scope, bool priv);
        bool add_var(const string& name, const string& scope);
        void add_var(const string& name);
        void add_scope(const string& name);
        int check_visibility(const string& name, const string& scope);
        Global_Table();
        ~Global_Table();
};

class Parser{
    // keeps track of symbol tables in each scope
    Global_Table *sym_table;
    LexicalAnalyzer lexer;
    // keeps track of scope
    vector<string> scopes;
    // keeps track of var visibility
    vector<string> visibility;
    string parse_output;
    bool error_flag;

    public:
        Parser();
        ~Parser();
        void parse_var();
        void parse_stmt();
        void parse_scope();
        void parse_public();
        void parse_private();
        void parse();
        void print_resolutions();
        string find_public_var(const string& name);
        string find_public_var(const string&& name);
};




#include "symbol_table.h"


SymbolTable::SymbolTable(const string& name):scope_name(name), var_names(unordered_map<string, bool>()){}

void SymbolTable::add_var(const string& name, bool priv = false){
    var_names[name] = priv;
}

bool SymbolTable::find_var(const string& name){
    return var_names.find(name)!=var_names.end();
}


// assumes var is in scope
bool SymbolTable::check_var_visibility(const string& name){
    // returns true if var is private
    return var_names[name];
}


string SymbolTable::get_scope(){
    return scope_name;
}





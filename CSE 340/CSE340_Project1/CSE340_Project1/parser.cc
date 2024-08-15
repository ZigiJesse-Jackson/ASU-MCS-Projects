#include "parser.h"
#include "lexer.h"
#include <iostream>

using namespace std;

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


Global_Table::Global_Table(){
    global = "global";
    tables[global] = new SymbolTable(global);
}
Global_Table::~Global_Table(){
    for(pair<string, SymbolTable*> p: tables){
        delete p.second;
    }
}
bool Global_Table::find_var(const string& name){
    if(tables[global]->find_var(name)) return true;
    // var DNE
    return false;
}

bool Global_Table::find_var(const string& name, const string& scope){
    // scope DNE
    if(tables.find(scope)==tables.end()) return false;
    if(tables[scope]->find_var(name)) return true;
    // var DNE
    return false;
}



void Global_Table::add_var(const string& name){
    tables[global]->add_var(name);
}

bool Global_Table::add_var(const string& name, const string& scope){
    if(tables.find(scope)==tables.end()) return false;
    tables[scope]->add_var(name);
    return true;
}


bool Global_Table::add_var(const string& name, const string& scope, bool priv){
    if(tables.find(scope)==tables.end()) return false;
    tables[scope]->add_var(name, priv);
    return true;
}




void Global_Table::add_scope(const string& scope){
    tables[scope] =  new SymbolTable(scope);
}



int Global_Table::check_visibility(const string& name, const string& scope){
    // var is present in scope
    if(find_var(name, scope)){
        // var is public
        if(!tables[scope]->check_var_visibility(name)) return 1;
        // var is private
        return -1;
    }
    return 0;
}


Parser::Parser(){
    sym_table = new Global_Table();
    error_flag = false;
    parse_output = "";
    scopes.push_back("global");
    visibility.push_back("public");
}

Parser::~Parser(){
    delete sym_table;
}




string Parser::find_public_var(const string& name){
    for(int i = scopes.size()-1; i>=0;i--){
        if(sym_table->check_visibility(name, scopes[i])==1) return scopes[i];
    }
    return "?";
}

string Parser::find_public_var(const string&& name){
    for(int i = scopes.size()-1; i>=0;i--){
        if(sym_table->check_visibility(name, scopes[i])==1) return scopes[i];
    }
    return "?";
}

void Parser::parse_var(){
    Token curr_t = lexer.GetToken();
    Token next_t = lexer.Peek();
    if(curr_t.token_type==ID){
        // add curr ID name as var to curr scope
        // check visibility for var initialization in curr scope
        if(visibility.back()=="public"){
            sym_table->add_var(curr_t.lexeme, scopes.back());
        }
        else sym_table->add_var(curr_t.lexeme, scopes.back(), true);

        switch(next_t.token_type){
            case(COMMA):
            // get comma so parse just deals with ID as first valid token
                lexer.GetToken();
                parse_var();
                break;
            case(SEMICOLON):
            // get semicolon so parse just deals with ID as first valid token
                lexer.GetToken();
                parse();
                break;
            default:
                error_flag = true;
                return;
        }
    }
    else {
        error_flag = true;
        return;
    }
}

void Parser::parse_stmt(){
    Token curr_t = lexer.GetToken();
    if(curr_t.token_type!=ID){
        error_flag = true;    
        return;
    }
    else{
        Token lhs = curr_t;
        curr_t = lexer.GetToken();
        if(curr_t.token_type!=EQUAL){
            error_flag = true;
            return;
        }
        else{
            curr_t = lexer.GetToken();
            if(curr_t.token_type!=ID){
                error_flag = true;
                return;
            }
            else{
                Token rhs = curr_t;
                curr_t = lexer.GetToken();
                // assignment can't be made unless semicolon is the next
                // token
                if(curr_t.token_type!=SEMICOLON){
                    error_flag = true;
                    return;
                }
                // check previous scope for most recent matching var with 
                string most_recent_l = find_public_var(lhs.lexeme);
                string most_recent_r = find_public_var(rhs.lexeme);
                string resolution = "";

                // find scope of lhs
                // check curr scope first
                if(sym_table->find_var(lhs.lexeme, scopes.back()))resolution+=scopes.back()+"."+lhs.lexeme;
                // public var found in earlier scope or not resolved
                else if(most_recent_l!="global")resolution+= most_recent_l+"."+lhs.lexeme;
                // var in global scope
                else resolution+="::"+lhs.lexeme;
                
                resolution+=" = ";

                // find scope of rhs
                // check curr scope first
                if(sym_table->find_var(rhs.lexeme, scopes.back()))resolution+=scopes.back()+"."+rhs.lexeme;
                // public var found in earlier scope or not resolved
                else if(most_recent_r!="global")resolution+= most_recent_r+"."+rhs.lexeme;
                // var in global scope
                else resolution+="::"+rhs.lexeme;
                resolution+="\n";
                parse_output+=resolution;
                parse();
            }
        }
    }
}

void Parser::parse_public(){
    visibility.push_back("public");
    Token curr_t = lexer.GetToken();
    if(curr_t.token_type!=COLON){
        error_flag = true;
        return;
    }
    else{
        parse_var();
    }
}

void Parser::parse_private(){
    visibility.push_back("private");
    Token curr_t = lexer.GetToken();

    if(curr_t.token_type!=COLON){
        error_flag = true;
        return;
    }
    else{
        parse_var();
    }
}

void Parser::parse_scope(){
    Token curr_t = lexer.GetToken();
    switch(curr_t.token_type){
        case(PUBLIC):
            parse_public();
            break;
        case(PRIVATE):
            parse_private();
            break;
        case(ID):
            lexer.UngetToken(curr_t);
            parse();
            break;
        default:
            error_flag = true;
            cout<<"Unrecognized token in scope"<<endl;
            break;
    }
}

void Parser::print_resolutions(){
    if(error_flag){
        cout<<"Syntax Error"<<endl;
        exit(1);
    }
    cout<<parse_output;
}

void Parser::parse(){
    Token curr_t = lexer.GetToken();

    if(curr_t.token_type == ID){
        Token next_t = lexer.Peek();
        bool added = false;
        switch(next_t.token_type){
            case(COMMA):
            // add curr ID name as var to curr scope
            
                sym_table->add_var(curr_t.lexeme, scopes.back());

            // get comma so parse_var just deals with ID as first token
                lexer.GetToken();
                parse_var();
                break;
            case(LBRAC):
            // add curr ID name as scope new scope
                scopes.push_back(curr_t.lexeme);
            // get left curly brace so parse_scope deals with ID, PUBLIC, OR PRIVATE
            // as first valid tokens
                lexer.GetToken();
                sym_table->add_scope(curr_t.lexeme);
                parse_scope();
                break;
            case(SEMICOLON):
            // add curr ID name as scope new scope
                sym_table->add_var(curr_t.lexeme, scopes.back());
            // get comma so parse just deals with ID as first valid token
                lexer.GetToken();
                parse();
                break;
            case(EQUAL):
            // unget ID so parse_stmt deals with ID as first valid token
                lexer.UngetToken(curr_t);
                parse_stmt();
                break;
            default:
                error_flag = true;
                break;   
        }
    }
    else if(curr_t.token_type == PRIVATE){
        // to ensure that private is within nested scope
        if(scopes.size()>1){
            // parse_private deals with COLON as first valid token
            parse_private();
        }
        else{
            error_flag = true;
            return;
        }
    }

    else if(curr_t.token_type == RBRAC){
        // to ensure that private is within nested scope
        if(scopes.size()>1){
            // remove curr scope
            scopes.pop_back();
            // parse deals with ID as first valid token
            parse();
        }else{
            error_flag = true;
            return;
        }
    }

    else if(curr_t.token_type == END_OF_FILE){
        // EOF reached whilst still in a non-global scope
        if(scopes.size()>1){
            error_flag = true;
            return;
        }
        
    }else{
        error_flag = true;
    }
}

int main(){
    Parser parser;
    parser.parse();
    parser.print_resolutions();
    return 0;
}
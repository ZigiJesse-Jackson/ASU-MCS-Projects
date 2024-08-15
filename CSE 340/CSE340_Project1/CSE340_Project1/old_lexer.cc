/*
 * Copyright (C) Rida Bazzi, 2016
 *
 * Do not share this file with anyone
 */
#include <iostream>
#include <istream>
#include <vector>
#include <unordered_set>
#include <string>
#include <cctype>

#include "old_lexer.h"
#include "inputbuf.h"

using namespace std;

string reserved[] = { "END_OF_FILE",
    "IF", "WHILE", "DO", "THEN", "PRINT",
    "PLUS", "MINUS", "DIV", "MULT",
    "EQUAL", "COLON", "COMMA", "SEMICOLON",
    "LBRAC", "RBRAC", "LPAREN", "RPAREN",
    "NOTEQUAL", "GREATER", "LESS", "LTEQ", "GTEQ",
    "DOT", "NUM", "ID", "REALNUM", "BASE08NUM", "BASE16NUM", "ERROR" // TODO: Add labels for new token types here (as string)
};

unordered_set<char> base_char{'A', 'B', 'C', 'D', 'E', 'F'}; 

#define KEYWORDS_COUNT 5
string keyword[] = { "IF", "WHILE", "DO", "THEN", "PRINT" };

void Token::Print()
{
    cout << "{" << this->lexeme << " , "
         << reserved[(int) this->token_type] << " , "
         << this->line_no << "}\n";
}

LexicalAnalyzer::LexicalAnalyzer()
{
    this->line_no = 1;
    tmp.lexeme = "";
    tmp.line_no = 1;
    tmp.token_type = ERROR;
}

bool LexicalAnalyzer::SkipSpace()
{
    char c;
    bool space_encountered = false;

    input.GetChar(c);
    line_no += (c == '\n');

    while (!input.EndOfInput() && isspace(c)) {
        space_encountered = true;
        input.GetChar(c);
        line_no += (c == '\n');
    }

    if (!input.EndOfInput()) {
        input.UngetChar(c);
    }
    return space_encountered;
}

bool LexicalAnalyzer::IsKeyword(string s)
{
    for (int i = 0; i < KEYWORDS_COUNT; i++) {
        if (s == keyword[i]) {
            return true;
        }
    }
    return false;
}

TokenType LexicalAnalyzer::FindKeywordIndex(string s)
{
    for (int i = 0; i < KEYWORDS_COUNT; i++) {
        if (s == keyword[i]) {
            return (TokenType) (i + 1);
        }
    }
    return ERROR;
}

Token LexicalAnalyzer::ScanNumber()
{
    char c;

    input.GetChar(c);
    bool isBase8 = true; // checks for valid base08 number
    if (isdigit(c)) {
        if (c == '0') {
            tmp.lexeme = "0";
        } else {
            tmp.lexeme = "";
            while (!input.EndOfInput() && isdigit(c)) {
                if(c-'0'>7) isBase8 = false;
                tmp.lexeme += c;
                input.GetChar(c);
            }
            if (!input.EndOfInput()) {
                input.UngetChar(c);
            }
        }
        // TODO: You can check for REALNUM, BASE08NUM and BASE16NUM here!
        input.GetChar(c);
        // checking for REAL NUM
        if(c=='.'){
            input.GetChar(c);
            // check next char is digit
            if(isdigit(c)){
                tmp.lexeme+=".";
                while (!input.EndOfInput() && isdigit(c)) {
                    tmp.lexeme += c;
                    input.GetChar(c);
                }
                if (!input.EndOfInput()) {
                    input.UngetChar(c);
                }
                tmp.token_type = REALNUM;
                tmp.line_no = line_no;
                return tmp;
            }
            //next char not a digit
            else{
                input.UngetChar(c);
                input.UngetChar('.');
            }  
        }
        // checking for Base Nums
        else if(base_char.find(c)!=base_char.end() || c=='x'){
            string poss_base="";
            if(c!='x'){
                // try parse base num body
                while(!input.EndOfInput() && (isdigit(c)||base_char.find(c)!=base_char.end())){
                    poss_base+=c;
                    input.GetChar(c);
                }
            }
            if(c=='x'){
                string base_type="";
                int i = 0;
                // try parse base num signature
                while(!input.EndOfInput() && i<3){
                    base_type+=c;
                    input.GetChar(c);
                    i++;
                }
                
                // EOF (EOL to be more exact) before we get basenum signature
                if(i<3){
                    input.UngetChar(c);
                    poss_base+=base_type;
                    while(poss_base!=""){
                        input.UngetChar(poss_base.back());
                        poss_base.pop_back();
                    } 
                }
                // base08 num
                else if(base_type=="x08" && isBase8){
                    poss_base+=base_type;
                    tmp.lexeme+=poss_base;
                    tmp.token_type = BASE08NUM;
                    tmp.line_no = line_no;
                    if(!input.EndOfInput()){
                        input.UngetChar(c);
                    } 
                    return tmp;
                }
                // base16 num
                else if(base_type=="x16"){
                    poss_base+=base_type;
                    tmp.lexeme+=poss_base;
                    tmp.token_type = BASE16NUM;
                    tmp.line_no = line_no;
                    if(!input.EndOfInput()){
                        input.UngetChar(c);
                    } 
                    return tmp;
                }
                else{
                    input.UngetChar(c);
                    poss_base+=base_type;
                    while(poss_base!=""){
                        input.UngetChar(poss_base.back());
                        poss_base.pop_back();
                    }
                }
                
            }// EOF reached before valid parse
            else{
                input.UngetChar(c);
                while(poss_base!=""){
                    input.UngetChar(poss_base.back());
                    poss_base.pop_back();
                }
            }
               
        }
        // subsequent char was not a DOT or base char
        else if(!input.EndOfInput()){
            input.UngetChar(c);
        }
        tmp.token_type = NUM;
        tmp.line_no = line_no;
        return tmp;
    } else {
        if (!input.EndOfInput()) {
            input.UngetChar(c);
        }
        tmp.lexeme = "";
        tmp.token_type = ERROR;
        tmp.line_no = line_no;
        return tmp;
    }
}

Token LexicalAnalyzer::ScanIdOrKeyword()
{
    char c;
    input.GetChar(c);

    if (isalpha(c)) {
        tmp.lexeme = "";
        while (!input.EndOfInput() && isalnum(c)) {
            tmp.lexeme += c;
            input.GetChar(c);
        }
        if (!input.EndOfInput()) {
            input.UngetChar(c);
        }
        tmp.line_no = line_no;
        if (IsKeyword(tmp.lexeme))
            tmp.token_type = FindKeywordIndex(tmp.lexeme);
        else
            tmp.token_type = ID;
    } else {
        if (!input.EndOfInput()) {
            input.UngetChar(c);
        }
        tmp.lexeme = "";
        tmp.token_type = ERROR;
    }
    return tmp;
}

// you should unget tokens in the reverse order in which they
// are obtained. If you execute
//
//    t1 = lexer.GetToken();
//    t2 = lexer.GetToken();
//    t3 = lexer.GetToken();
//
// in this order, you should execute
//
//    lexer.UngetToken(t3);
//    lexer.UngetToken(t2);
//    lexer.UngetToken(t1);
//
// if you want to unget all three tokens. Note that it does not
// make sense to unget t1 without first ungetting t2 and t3
//
TokenType LexicalAnalyzer::UngetToken(Token tok)
{
    tokens.push_back(tok);;
    return tok.token_type;
}

Token LexicalAnalyzer::GetToken()
{
    char c;

    // if there are tokens that were previously
    // stored due to UngetToken(), pop a token and
    // return it without reading from input
    if (!tokens.empty()) {
        tmp = tokens.back();
        tokens.pop_back();
        return tmp;
    }

    SkipSpace();
    tmp.lexeme = "";
    tmp.line_no = line_no;
    input.GetChar(c);
    switch (c) {
        case '.':
            tmp.token_type = DOT;
            return tmp;
        case '+':
            tmp.token_type = PLUS;
            return tmp;
        case '-':
            tmp.token_type = MINUS;
            return tmp;
        case '/':
            tmp.token_type = DIV;
            return tmp;
        case '*':
            tmp.token_type = MULT;
            return tmp;
        case '=':
            tmp.token_type = EQUAL;
            return tmp;
        case ':':
            tmp.token_type = COLON;
            return tmp;
        case ',':
            tmp.token_type = COMMA;
            return tmp;
        case ';':
            tmp.token_type = SEMICOLON;
            return tmp;
        case '[':
            tmp.token_type = LBRAC;
            return tmp;
        case ']':
            tmp.token_type = RBRAC;
            return tmp;
        case '(':
            tmp.token_type = LPAREN;
            return tmp;
        case ')':
            tmp.token_type = RPAREN;
            return tmp;
        case '<':
            input.GetChar(c);
            if (c == '=') {
                tmp.token_type = LTEQ;
            } else if (c == '>') {
                tmp.token_type = NOTEQUAL;
            } else {
                if (!input.EndOfInput()) {
                    input.UngetChar(c);
                }
                tmp.token_type = LESS;
            }
            return tmp;
        case '>':
            input.GetChar(c);
            if (c == '=') {
                tmp.token_type = GTEQ;
            } else {
                if (!input.EndOfInput()) {
                    input.UngetChar(c);
                }
                tmp.token_type = GREATER;
            }
            return tmp;
        default:
            if (isdigit(c)) {
                input.UngetChar(c);
                return ScanNumber();
            } else if (isalpha(c)) {
                input.UngetChar(c);
                return ScanIdOrKeyword();
            } else if (input.EndOfInput())
                tmp.token_type = END_OF_FILE;
            else
                tmp.token_type = ERROR;

            return tmp;
    }
}

int main()
{
    LexicalAnalyzer lexer;
    Token token;

    token = lexer.GetToken();
    token.Print();
    while (token.token_type != END_OF_FILE)
    {
        token = lexer.GetToken();
        token.Print();
    }
}
